"""Metrics collection for ML services.

This module provides metrics collection and monitoring capabilities
for ML service operations.
"""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OperationMetrics:
    """Metrics for a single operation."""

    name: str
    duration_ms: float
    memory_mb: float
    batch_size: Optional[int] = None
    error_count: int = 0
    success: bool = True
    metadata: Dict[str, Any] = None


class MetricsCollector:
    """Collects and manages service metrics."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._metrics: Dict[str, List[OperationMetrics]] = {}
        self._current_operation: Optional[str] = None
        self._start_time: Optional[float] = None

    def get_metrics(self, operation: str) -> List[OperationMetrics]:
        """Get metrics for an operation.

        Args:
            operation: Operation name

        Returns:
            List of operation metrics
        """
        return self._metrics.get(operation, [])

    def record_metric(self, metric: OperationMetrics) -> None:
        """Record an operation metric.

        Args:
            metric: Operation metric to record
        """
        if metric.name not in self._metrics:
            self._metrics[metric.name] = []
        self._metrics[metric.name].append(metric)
        logger.debug(f"Recorded metric for {metric.name}: {metric.duration_ms}ms")

    @contextmanager
    def track_operation(
        self,
        name: str,
        batch_size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Track an operation's metrics.

        Args:
            name: Operation name
            batch_size: Optional batch size
            metadata: Optional operation metadata

        Yields:
            None
        """
        self._current_operation = name
        self._start_time = time.time()
        success = True
        error_count = 0

        try:
            yield
        except Exception as e:
            success = False
            error_count = 1
            raise e
        finally:
            if self._start_time is not None:
                duration_ms = (time.time() - self._start_time) * 1000
                memory_mb = self._get_memory_usage()

                metric = OperationMetrics(
                    name=name,
                    duration_ms=duration_ms,
                    memory_mb=memory_mb,
                    batch_size=batch_size,
                    error_count=error_count,
                    success=success,
                    metadata=metadata or {},
                )
                self.record_metric(metric)
                logger.debug(f"Operation {name} completed in {duration_ms:.2f}ms")

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            logger.warning("psutil not available for memory tracking")
            return 0.0
