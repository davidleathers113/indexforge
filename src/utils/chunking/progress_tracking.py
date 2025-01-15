"""Progress tracking utilities for batch operations.

This module provides tools for tracking progress of long-running batch operations,
including completion percentage, ETA, and performance metrics.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of batch operations."""

    CHUNKING = auto()  # Text chunking operations
    REFERENCE_CREATION = auto()  # Reference creation/update
    CLASSIFICATION = auto()  # Reference classification
    CACHE_WARMUP = auto()  # Cache pre-warming
    BATCH_IMPORT = auto()  # Batch data import


@dataclass
class ProgressMetrics:
    """Metrics for batch operation progress."""

    items_total: int = 0
    items_completed: int = 0
    items_failed: int = 0
    start_time: float = field(default_factory=time.time)
    last_update_time: float = field(default_factory=time.time)
    processing_rate: float = 0.0  # Items per second
    estimated_remaining_seconds: float = 0.0


@dataclass
class BatchMetrics:
    """Metrics for batch processing performance."""

    batch_size: int = 0
    batches_completed: int = 0
    avg_batch_duration_ms: float = 0.0
    min_batch_duration_ms: float = float("inf")
    max_batch_duration_ms: float = 0.0
    total_duration_ms: float = 0.0


class ProgressTracker:
    """Tracks progress of batch operations."""

    def __init__(
        self,
        operation_type: OperationType,
        total_items: int,
        batch_size: Optional[int] = None,
        update_interval: float = 1.0,
    ):
        """Initialize progress tracker.

        Args:
            operation_type: Type of batch operation
            total_items: Total number of items to process
            batch_size: Size of each batch (if applicable)
            update_interval: Minimum seconds between progress updates
        """
        self.operation_type = operation_type
        self.batch_size = batch_size
        self.update_interval = update_interval
        self.progress = ProgressMetrics(items_total=total_items)
        self.batch_metrics = BatchMetrics(batch_size=batch_size or 0)
        self._batch_start_time: Optional[float] = None

    def start_batch(self) -> None:
        """Record start of a new batch."""
        self._batch_start_time = time.time()

    def complete_batch(self, items_completed: int, items_failed: int = 0) -> None:
        """Record completion of a batch.

        Args:
            items_completed: Number of items successfully completed
            items_failed: Number of items that failed
        """
        if self._batch_start_time is None:
            raise ValueError("Batch not started")

        # Update batch metrics
        batch_duration_ms = (time.time() - self._batch_start_time) * 1000
        self.batch_metrics.batches_completed += 1
        self.batch_metrics.total_duration_ms += batch_duration_ms
        self.batch_metrics.min_batch_duration_ms = min(
            self.batch_metrics.min_batch_duration_ms, batch_duration_ms
        )
        self.batch_metrics.max_batch_duration_ms = max(
            self.batch_metrics.max_batch_duration_ms, batch_duration_ms
        )
        self.batch_metrics.avg_batch_duration_ms = (
            self.batch_metrics.total_duration_ms / self.batch_metrics.batches_completed
        )

        # Update progress metrics
        self.progress.items_completed += items_completed
        self.progress.items_failed += items_failed
        current_time = time.time()

        # Update processing rate and ETA if enough time has passed
        if current_time - self.progress.last_update_time >= self.update_interval:
            elapsed_time = current_time - self.progress.start_time
            if elapsed_time > 0:
                self.progress.processing_rate = self.progress.items_completed / elapsed_time
                remaining_items = self.progress.items_total - self.progress.items_completed
                if self.progress.processing_rate > 0:
                    self.progress.estimated_remaining_seconds = (
                        remaining_items / self.progress.processing_rate
                    )

            self.progress.last_update_time = current_time
            self._log_progress()

        self._batch_start_time = None

    def _log_progress(self) -> None:
        """Log current progress."""
        percent_complete = (
            self.progress.items_completed / self.progress.items_total * 100
            if self.progress.items_total > 0
            else 0
        )

        logger.info(
            "%s Progress: %.1f%% (%d/%d items) - %.1f items/sec - ETA: %s - Failed: %d",
            self.operation_type.name,
            percent_complete,
            self.progress.items_completed,
            self.progress.items_total,
            self.progress.processing_rate,
            self._format_duration(self.progress.estimated_remaining_seconds),
            self.progress.items_failed,
        )

        if self.batch_metrics.batches_completed > 0:
            logger.debug(
                "Batch Metrics: %d batches, Avg: %.1fms, Min: %.1fms, Max: %.1fms",
                self.batch_metrics.batches_completed,
                self.batch_metrics.avg_batch_duration_ms,
                self.batch_metrics.min_batch_duration_ms,
                self.batch_metrics.max_batch_duration_ms,
            )

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string
        """
        if seconds < 0 or not seconds:
            return "unknown"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def get_progress_summary(self) -> Dict:
        """Get summary of current progress.

        Returns:
            Dictionary with progress summary
        """
        percent_complete = (
            self.progress.items_completed / self.progress.items_total * 100
            if self.progress.items_total > 0
            else 0
        )

        return {
            "operation_type": self.operation_type.name,
            "percent_complete": percent_complete,
            "items_completed": self.progress.items_completed,
            "items_total": self.progress.items_total,
            "items_failed": self.progress.items_failed,
            "processing_rate": self.progress.processing_rate,
            "eta": self._format_duration(self.progress.estimated_remaining_seconds),
            "elapsed": self._format_duration(time.time() - self.progress.start_time),
            "batch_metrics": {
                "batch_size": self.batch_metrics.batch_size,
                "batches_completed": self.batch_metrics.batches_completed,
                "avg_duration_ms": self.batch_metrics.avg_batch_duration_ms,
                "min_duration_ms": self.batch_metrics.min_batch_duration_ms,
                "max_duration_ms": self.batch_metrics.max_batch_duration_ms,
            },
        }


def track_batch_operation(tracker: ProgressTracker):
    """Decorator to track progress of batch operations.

    Args:
        tracker: Progress tracker to use
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            tracker.start_batch()
            try:
                result = func(*args, **kwargs)
                # Assume result contains completed/failed counts
                completed = getattr(result, "completed", 1)
                failed = getattr(result, "failed", 0)
                tracker.complete_batch(completed, failed)
                return result
            except Exception:
                tracker.complete_batch(0, 1)
                raise

        return wrapper

    return decorator
