"""Core metrics interfaces.

This module defines the interfaces for metrics collection across different services.
It provides protocols for storage metrics, operation metrics, and related functionality.
"""

from typing import Protocol


class StorageMetrics(Protocol):
    """Protocol for storage metrics collection."""

    def get_storage_usage(self) -> dict[str, int]:
        """Get storage usage metrics.

        Returns:
            Dict[str, int]: Dictionary containing:
                - total_bytes: Total storage used in bytes
                - document_count: Number of stored documents
                - chunk_count: Number of stored chunks
                - reference_count: Number of stored references
        """
        ...

    def get_operation_counts(self) -> dict[str, int]:
        """Get operation count metrics.

        Returns:
            Dict[str, int]: Dictionary containing counts for:
                - reads: Number of read operations
                - writes: Number of write operations
                - updates: Number of update operations
                - deletes: Number of delete operations
        """
        ...


class MetricsProvider(Protocol):
    """Protocol for metrics provider implementations."""

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric.

        Args:
            name: Name of the counter to increment
            value: Value to increment by (default: 1)
        """
        ...

    def record_value(self, name: str, value: float) -> None:
        """Record a value metric.

        Args:
            name: Name of the metric
            value: Value to record
        """
        ...

    def start_timer(self, name: str) -> None:
        """Start a timer for an operation.

        Args:
            name: Name of the timer
        """
        ...

    def stop_timer(self, name: str) -> float:
        """Stop a timer and get the elapsed time.

        Args:
            name: Name of the timer to stop

        Returns:
            float: Elapsed time in seconds
        """
        ...
