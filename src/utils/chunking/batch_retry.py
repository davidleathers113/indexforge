"""Batch retry utilities for handling failed operations.

This module provides tools for retrying failed batch operations with configurable
retry policies, exponential backoff, and detailed retry metrics.
"""

import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .progress_tracking import OperationType, ProgressTracker

logger = logging.getLogger(__name__)

T = TypeVar("T")  # Type variable for batch operation results


class RetryStrategy(Enum):
    """Retry strategies for failed operations."""

    LINEAR = auto()  # Fixed delay between retries
    EXPONENTIAL = auto()  # Exponential backoff with jitter
    FIBONACCI = auto()  # Fibonacci sequence-based delays


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3  # Maximum number of retry attempts
    initial_delay: float = 1.0  # Initial delay in seconds
    max_delay: float = 60.0  # Maximum delay between retries
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: float = 0.1  # Random jitter factor (0-1)
    timeout: Optional[float] = None  # Overall timeout for all retries
    failure_callback: Optional[Callable[[Any, Exception], None]] = (
        None  # Callback for persistent failures
    )


@dataclass
class RetryMetrics:
    """Metrics for retry operations."""

    total_retries: int = 0
    successful_retries: int = 0
    failed_retries: int = 0
    total_retry_time: float = 0.0
    retry_delays: List[float] = field(default_factory=list)
    retry_timestamps: List[float] = field(default_factory=list)
    error_types: Dict[str, int] = field(default_factory=lambda: {})


@dataclass
class BatchItem:
    """Represents an item in a batch with its retry state."""

    data: Any
    attempt: int = 0
    last_error: Optional[Exception] = None
    next_retry_time: float = 0.0


class BatchRetryManager:
    """Manages retries for failed batch operations."""

    def __init__(
        self,
        operation_type: OperationType,
        config: RetryConfig,
        progress_tracker: Optional[ProgressTracker] = None,
    ):
        """Initialize batch retry manager.

        Args:
            operation_type: Type of batch operation
            config: Retry configuration
            progress_tracker: Optional progress tracker to update
        """
        self.operation_type = operation_type
        self.config = config
        self.progress_tracker = progress_tracker
        self.metrics = RetryMetrics()
        self._start_time = time.time()
        self._fib_cache: Dict[int, int] = {0: 0, 1: 1}  # Cache for Fibonacci numbers

    def _fibonacci(self, n: int) -> int:
        """Calculate nth Fibonacci number using dynamic programming.

        Args:
            n: Position in Fibonacci sequence

        Returns:
            nth Fibonacci number
        """
        if n in self._fib_cache:
            return self._fib_cache[n]

        # Calculate Fibonacci numbers iteratively
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
            self._fib_cache[_ + 2] = b  # Cache intermediate results

        return b

    def calculate_next_delay(self, attempt: int) -> float:
        """Calculate delay for next retry attempt.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds for next retry
        """
        base_delay = self.config.initial_delay

        if self.config.strategy == RetryStrategy.LINEAR:
            delay = base_delay
            logger.debug(
                "Calculated linear delay: %.2f seconds for attempt %d",
                delay,
                attempt,
            )
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = base_delay * (2**attempt)
            logger.debug(
                "Calculated exponential delay: %.2f seconds for attempt %d",
                delay,
                attempt,
            )
        else:  # FIBONACCI
            delay = base_delay * self._fibonacci(attempt + 1)
            logger.debug(
                "Calculated Fibonacci delay: %.2f seconds for attempt %d",
                delay,
                attempt,
            )

        # Apply jitter
        jitter = random.uniform(-self.config.jitter, self.config.jitter)
        delay = delay * (1 + jitter)
        logger.debug("Applied jitter: %.2f seconds (%.2f%%)", delay, jitter * 100)

        # Ensure delay doesn't exceed max_delay
        final_delay = min(delay, self.config.max_delay)
        if final_delay != delay:
            logger.debug(
                "Delay capped at max_delay: %.2f seconds (original: %.2f)",
                final_delay,
                delay,
            )

        return final_delay

    def should_retry(self, item: BatchItem, current_time: float) -> bool:
        """Determine if an item should be retried.

        Args:
            item: Batch item to check
            current_time: Current timestamp

        Returns:
            True if item should be retried
        """
        if item.attempt >= self.config.max_retries:
            logger.debug(
                "Max retries exceeded for item: %s (attempts: %d/%d)",
                item.data,
                item.attempt,
                self.config.max_retries,
            )
            return False

        if self.config.timeout and (current_time - self._start_time) >= self.config.timeout:
            logger.debug(
                "Operation timeout exceeded: %.1f seconds",
                current_time - self._start_time,
            )
            return False

        can_retry = current_time >= item.next_retry_time
        if can_retry:
            logger.debug(
                "Item eligible for retry: %s (attempt %d/%d)",
                item.data,
                item.attempt + 1,
                self.config.max_retries,
            )
        return can_retry

    def process_batch(
        self,
        items: List[Any],
        operation: Callable[[Any], T],
        should_retry_error: Optional[Callable[[Exception], bool]] = None,
    ) -> List[T]:
        """Process a batch of items with retry logic.

        Args:
            items: List of items to process
            operation: Function to process each item
            should_retry_error: Optional function to determine if an error should trigger retry

        Returns:
            List of successfully processed results
        """
        logger.info(
            "Starting batch processing with %d items (max_retries=%d, strategy=%s)",
            len(items),
            self.config.max_retries,
            self.config.strategy.name,
        )

        batch_items = [BatchItem(data=item) for item in items]
        results: List[Optional[T]] = [None] * len(items)
        pending_items = list(range(len(items)))

        while pending_items and (
            not self.config.timeout or (time.time() - self._start_time) < self.config.timeout
        ):
            current_time = time.time()
            retry_candidates = [
                i for i in pending_items if self.should_retry(batch_items[i], current_time)
            ]

            if not retry_candidates:
                if all(batch_items[i].attempt >= self.config.max_retries for i in pending_items):
                    logger.warning(
                        "All pending items (%d) have exceeded max retries",
                        len(pending_items),
                    )
                    break
                time.sleep(0.1)  # Prevent tight loop
                continue

            # Process retry candidates
            for idx in retry_candidates:
                item = batch_items[idx]
                try:
                    if item.attempt > 0:
                        self.metrics.total_retries += 1
                        self.metrics.retry_timestamps.append(current_time)
                        logger.debug(
                            "Retrying item %d (attempt %d/%d)",
                            idx,
                            item.attempt + 1,
                            self.config.max_retries,
                        )

                    results[idx] = operation(item.data)

                    if item.attempt > 0:
                        self.metrics.successful_retries += 1
                        logger.info(
                            "Successfully processed item %d after %d retries",
                            idx,
                            item.attempt,
                        )

                    pending_items.remove(idx)

                    if self.progress_tracker:
                        self.progress_tracker.complete_batch(1, 0)

                except Exception as e:
                    item.attempt += 1
                    item.last_error = e

                    error_type = type(e).__name__
                    self.metrics.error_types[error_type] = (
                        self.metrics.error_types.get(error_type, 0) + 1
                    )

                    if item.attempt > 0:
                        self.metrics.failed_retries += 1

                    logger.debug(
                        "Operation failed for item %d: %s (%s)",
                        idx,
                        str(e),
                        error_type,
                    )

                    if should_retry_error and not should_retry_error(e):
                        logger.warning(
                            "Non-retryable error for item %d: %s (%s)",
                            idx,
                            str(e),
                            error_type,
                        )
                        pending_items.remove(idx)
                        if self.progress_tracker:
                            self.progress_tracker.complete_batch(0, 1)
                        if self.config.failure_callback:
                            self.config.failure_callback(item.data, e)
                        continue

                    if item.attempt >= self.config.max_retries:
                        logger.error(
                            "Max retries exceeded for item %d: %s (%s)",
                            idx,
                            str(e),
                            error_type,
                        )
                        pending_items.remove(idx)
                        if self.progress_tracker:
                            self.progress_tracker.complete_batch(0, 1)
                        if self.config.failure_callback:
                            self.config.failure_callback(item.data, e)
                        continue

                    delay = self.calculate_next_delay(item.attempt)
                    item.next_retry_time = current_time + delay
                    self.metrics.retry_delays.append(delay)

                    logger.info(
                        "Scheduling retry %d/%d for item %d in %.1f seconds",
                        item.attempt,
                        self.config.max_retries,
                        idx,
                        delay,
                    )

        self.metrics.total_retry_time = time.time() - self._start_time
        logger.info(
            "Batch processing completed: %d succeeded, %d failed, %.1f seconds elapsed",
            len([r for r in results if r is not None]),
            len(items) - len([r for r in results if r is not None]),
            self.metrics.total_retry_time,
        )

        return [r for r in results if r is not None]

    def get_metrics_summary(self) -> Dict:
        """Get summary of retry metrics.

        Returns:
            Dictionary with retry metrics summary
        """
        success_rate = (
            (self.metrics.successful_retries / self.metrics.total_retries * 100)
            if self.metrics.total_retries > 0
            else 0
        )

        avg_delay = (
            sum(self.metrics.retry_delays) / len(self.metrics.retry_delays)
            if self.metrics.retry_delays
            else 0
        )

        return {
            "total_retries": self.metrics.total_retries,
            "successful_retries": self.metrics.successful_retries,
            "failed_retries": self.metrics.failed_retries,
            "success_rate": success_rate,
            "total_retry_time": self.metrics.total_retry_time,
            "avg_retry_delay": avg_delay,
            "error_types": dict(self.metrics.error_types),
        }
