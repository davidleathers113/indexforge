"""Storage metrics service implementation."""

from typing import Dict

from src.core.interfaces.storage import StorageMetrics
from src.core.metrics import ServiceMetricsCollector
from src.services.base import BaseService


class StorageMetricsService(StorageMetrics, BaseService):
    """Implementation of storage metrics collection."""

    def __init__(self) -> None:
        """Initialize storage metrics service."""
        BaseService.__init__(self)
        self._metrics = ServiceMetricsCollector(
            service_name="storage",
            max_history=5000,
            memory_threshold_mb=500,
        )
        self._storage_stats: Dict[str, int] = {
            "total_bytes": 0,
            "document_count": 0,
            "chunk_count": 0,
            "reference_count": 0,
        }
        self._operation_counts: Dict[str, int] = {
            "reads": 0,
            "writes": 0,
            "updates": 0,
            "deletes": 0,
        }

    def get_storage_usage(self) -> Dict[str, int]:
        """Get storage usage metrics.

        Returns:
            Dict[str, int]: Dictionary containing:
                - total_bytes: Total storage used in bytes
                - document_count: Number of stored documents
                - chunk_count: Number of stored chunks
                - reference_count: Number of stored references
        """
        with self._metrics.measure_operation("get_storage_usage"):
            return self._storage_stats.copy()

    def get_operation_counts(self) -> Dict[str, int]:
        """Get operation count metrics.

        Returns:
            Dict[str, int]: Dictionary containing counts for:
                - reads: Number of read operations
                - writes: Number of write operations
                - updates: Number of update operations
                - deletes: Number of delete operations
        """
        with self._metrics.measure_operation("get_operation_counts"):
            return self._operation_counts.copy()

    def increment_storage_stat(self, stat_name: str, amount: int = 1) -> None:
        """Increment a storage statistic.

        Args:
            stat_name: Name of the statistic to increment
            amount: Amount to increment by (default: 1)
        """
        if stat_name in self._storage_stats:
            self._storage_stats[stat_name] += amount

    def increment_operation_count(self, operation: str) -> None:
        """Increment an operation counter.

        Args:
            operation: Name of the operation counter to increment
        """
        if operation in self._operation_counts:
            self._operation_counts[operation] += 1

    def decrement_storage_stat(self, stat_name: str, amount: int = 1) -> None:
        """Decrement a storage statistic.

        Args:
            stat_name: Name of the statistic to decrement
            amount: Amount to decrement by (default: 1)
        """
        if stat_name in self._storage_stats:
            self._storage_stats[stat_name] = max(0, self._storage_stats[stat_name] - amount)

    def reset_metrics(self) -> None:
        """Reset all metrics to zero."""
        for key in self._storage_stats:
            self._storage_stats[key] = 0
        for key in self._operation_counts:
            self._operation_counts[key] = 0
        self._metrics.reset()
