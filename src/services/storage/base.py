"""Base storage service module.

This module provides the base implementation for storage services,
including metrics collection and error handling.
"""

from dataclasses import dataclass
from typing import Generic, TypeVar

from src.core.interfaces.metrics import MetricsProvider
from src.core.types.storage import StorageMetrics

T = TypeVar("T")


@dataclass
class BatchResult(Generic[T]):
    """Results of a batch operation."""

    successful: list[T]
    failed: list[tuple[T, Exception]]

    @property
    def success_count(self) -> int:
        """Get count of successful operations."""
        return len(self.successful)

    @property
    def failure_count(self) -> int:
        """Get count of failed operations."""
        return len(self.failed)

    @property
    def total_count(self) -> int:
        """Get total number of operations attempted."""
        return self.success_count + self.failure_count


class BatchConfig:
    """Configuration for batch operations."""

    def __init__(
        self, max_batch_size: int = 1000, memory_threshold_mb: int = 500, max_retries: int = 3
    ):
        """Initialize batch configuration.

        Args:
            max_batch_size: Maximum items per batch
            memory_threshold_mb: Memory threshold in MB
            max_retries: Maximum retry attempts
        """
        self.max_batch_size = max_batch_size
        self.memory_threshold_mb = memory_threshold_mb
        self.max_retries = max_retries

    def adjust_batch_size(self, current_memory_usage_mb: float) -> None:
        """Adjust batch size based on memory usage.

        Args:
            current_memory_usage_mb: Current memory usage in MB
        """
        if current_memory_usage_mb > self.memory_threshold_mb:
            self.max_batch_size = max(100, self.max_batch_size // 2)


class BaseStorageService:
    """Base class for storage services with metrics support."""

    def __init__(
        self,
        metrics: StorageMetrics | None = None,
        metrics_provider: MetricsProvider | None = None,
        batch_config: BatchConfig | None = None,
    ):
        """Initialize the base storage service.

        Args:
            metrics: Optional storage metrics collector
            metrics_provider: Optional metrics provider for detailed metrics
            batch_config: Optional batch operation configuration
        """
        self._metrics = metrics
        self._metrics_provider = metrics_provider
        self._batch_config = batch_config or BatchConfig()

    def _record_operation(self, operation: str) -> None:
        """Record an operation metric.

        Args:
            operation: Name of the operation
        """
        if self._metrics_provider:
            self._metrics_provider.increment_counter(f"storage.{operation}")

    def _time_operation(self, operation: str) -> None:
        """Start timing an operation.

        Args:
            operation: Name of the operation
        """
        if self._metrics_provider:
            self._metrics_provider.start_timer(f"storage.{operation}.duration")

    def _stop_timing(self, operation: str) -> float | None:
        """Stop timing an operation and get duration.

        Args:
            operation: Name of the operation

        Returns:
            Optional[float]: Duration in seconds if timing was started
        """
        if self._metrics_provider:
            return self._metrics_provider.stop_timer(f"storage.{operation}.duration")
        return None

    def process_batch(self, items: list[T], operation: str) -> BatchResult[T]:
        """Process a batch of items with metrics and error handling.

        Args:
            items: List of items to process
            operation: Name of the operation being performed

        Returns:
            BatchResult containing successful and failed items
        """
        results = BatchResult([], [])

        if not items:
            return results

        self._time_operation(f"batch_{operation}")

        for item in items:
            try:
                # Process individual item
                self._record_operation(operation)
                results.successful.append(item)
            except Exception as e:
                results.failed.append((item, e))

        duration = self._stop_timing(f"batch_{operation}")
        if duration and self._metrics_provider:
            self._metrics_provider.record_value(f"storage.{operation}.batch_duration", duration)

        return results
