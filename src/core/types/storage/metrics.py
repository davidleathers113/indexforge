"""Storage metrics protocol.

This module defines the protocol for storage metrics collection and reporting.
It provides a standardized interface for tracking storage operations and their performance.
"""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from src.core.settings import Settings


class StorageMetrics(Protocol):
    """Protocol for storage metrics collection.

    This protocol defines the interface for tracking and reporting storage
    operation metrics, including operation durations and performance data.
    """

    def __init__(self, settings: "Settings") -> None:
        """Initialize storage metrics.

        Args:
            settings: Storage configuration settings
        """
        pass

    def record_operation(self, operation: str, duration: float) -> None:
        """Record a storage operation and its duration.

        Args:
            operation: Name of the storage operation
            duration: Duration of the operation in seconds
        """
        pass

    def get_metrics(self) -> dict[str, list[float]]:
        """Get collected storage metrics.

        Returns:
            Dict[str, List[float]]: Dictionary mapping operation names to lists of durations
        """
        pass
