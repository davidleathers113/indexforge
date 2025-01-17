"""Storage metrics implementation.

This module provides metrics collection for storage operations, tracking
operation durations and frequencies for performance monitoring.
"""

import logging
import time
from collections import defaultdict
from typing import Dict, List

from ..models.settings import Settings

logger = logging.getLogger(__name__)


class StorageMetricsCollector:
    """Collects and manages storage operation metrics."""

    def __init__(self, settings: Settings) -> None:
        """Initialize metrics collector.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self._metrics: Dict[str, List[float]] = defaultdict(list)
        self._start_times: Dict[str, float] = {}
        logger.debug("Initialized storage metrics collector")

    def start_operation(self, operation: str) -> None:
        """Start timing an operation.

        Args:
            operation: Name of the operation to time
        """
        self._start_times[operation] = time.monotonic()
        logger.debug("Started timing operation: %s", operation)

    def end_operation(self, operation: str) -> None:
        """End timing an operation and record its duration.

        Args:
            operation: Name of the operation to end

        Raises:
            ValueError: If operation was not started
        """
        if operation not in self._start_times:
            raise ValueError(f"Operation {operation} was not started")

        duration = time.monotonic() - self._start_times[operation]
        self.record_operation(operation, duration)
        del self._start_times[operation]
        logger.debug("Ended operation %s (duration: %.3fs)", operation, duration)

    def record_operation(self, operation: str, duration: float) -> None:
        """Record a storage operation and its duration.

        Args:
            operation: Name of the storage operation
            duration: Duration of the operation in seconds
        """
        self._metrics[operation].append(duration)
        if len(self._metrics[operation]) > self.settings.max_metrics_history:
            self._metrics[operation].pop(0)
        logger.debug("Recorded operation %s (duration: %.3fs)", operation, duration)

    def get_metrics(self) -> Dict[str, List[float]]:
        """Get collected storage metrics.

        Returns:
            Dictionary mapping operation names to lists of durations
        """
        return dict(self._metrics)

    def get_average_duration(self, operation: str) -> float:
        """Get average duration for an operation.

        Args:
            operation: Operation name

        Returns:
            Average duration in seconds, or 0 if no metrics
        """
        durations = self._metrics.get(operation, [])
        return sum(durations) / len(durations) if durations else 0

    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        self._metrics.clear()
        self._start_times.clear()
        logger.debug("Cleared all metrics")
