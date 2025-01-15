"""Performance tracking for batch operations."""

from dataclasses import dataclass
import logging
from statistics import mean, median
import time
from typing import Dict, List, Optional

from .base import BaseMetrics

logger = logging.getLogger(__name__)


@dataclass
class BatchPerformanceMetrics:
    """Performance metrics for a single batch."""

    batch_size: int
    duration_seconds: float
    objects_per_second: float
    error_rate: float
    memory_usage_mb: Optional[float] = None


class BatchPerformanceTracker(BaseMetrics):
    """Tracks and analyzes batch performance for optimization."""

    def __init__(self, min_batch_size: int = 50, max_batch_size: int = 500, window_size: int = 10):
        """Initialize performance tracker.

        Args:
            min_batch_size: Minimum allowed batch size
            max_batch_size: Maximum allowed batch size
            window_size: Number of batches to analyze for optimization
        """
        super().__init__()
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.window_size = window_size
        self.metrics_history: List[BatchPerformanceMetrics] = []
        self.current_batch_start: Optional[float] = None
        self.current_batch_size: Optional[int] = None
        self.optimal_batch_size: int = min_batch_size

    def start_batch(self, batch_size: int) -> None:
        """Start timing a new batch operation."""
        self.current_batch_start = time.time()
        self.current_batch_size = batch_size

    def end_batch(
        self, successful_objects: int, failed_objects: int, memory_usage_mb: Optional[float] = None
    ) -> None:
        """Record metrics for completed batch."""
        if self.current_batch_start is None or self.current_batch_size is None:
            logger.warning("Cannot end batch: no batch currently in progress")
            return

        duration = time.time() - self.current_batch_start
        total_objects = successful_objects + failed_objects
        objects_per_second = total_objects / duration if duration > 0 else 0
        error_rate = failed_objects / total_objects if total_objects > 0 else 0

        metrics = BatchPerformanceMetrics(
            batch_size=self.current_batch_size,
            duration_seconds=duration,
            objects_per_second=objects_per_second,
            error_rate=error_rate,
            memory_usage_mb=memory_usage_mb,
        )

        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.window_size:
            self.metrics_history.pop(0)

        self._optimize_batch_size()
        self.notify_observers("throughput", objects_per_second)
        self.notify_observers("error_rate", error_rate)

        self.current_batch_start = None
        self.current_batch_size = None

    def get_optimal_batch_size(self) -> int:
        """Get the current optimal batch size.

        Returns:
            Optimal batch size for next operation
        """
        return self.optimal_batch_size

    def get_summary(self) -> Dict:
        """Get performance metrics summary."""
        if not self.metrics_history:
            return {"error": "No performance data available"}

        recent_metrics = self.metrics_history[-self.window_size :]
        return {
            "optimal_batch_size": self.optimal_batch_size,
            "throughput": {
                "mean": mean(m.objects_per_second for m in recent_metrics),
                "median": median(m.objects_per_second for m in recent_metrics),
                "min": min(m.objects_per_second for m in recent_metrics),
                "max": max(m.objects_per_second for m in recent_metrics),
            },
            "error_rates": {
                "mean": mean(m.error_rate for m in recent_metrics),
                "median": median(m.error_rate for m in recent_metrics),
                "min": min(m.error_rate for m in recent_metrics),
                "max": max(m.error_rate for m in recent_metrics),
            },
            "batch_sizes_used": sorted(set(m.batch_size for m in recent_metrics)),
            "total_batches_analyzed": len(self.metrics_history),
        }

    def _optimize_batch_size(self) -> None:
        """Optimize batch size based on recent performance metrics."""
        if len(self.metrics_history) < 2:
            return

        # Calculate performance metrics
        throughput = mean([m.objects_per_second for m in self.metrics_history])
        error_rate = median([m.error_rate for m in self.metrics_history])
        current_size = self.metrics_history[-1].batch_size

        # Adjust batch size based on performance
        if error_rate > 0.1:  # High error rate, reduce batch size
            self.optimal_batch_size = max(self.min_batch_size, int(current_size * 0.8))
        elif throughput > 100 and error_rate < 0.05:  # Good performance, try larger batches
            self.optimal_batch_size = min(self.max_batch_size, int(current_size * 1.2))
        else:  # Maintain current size
            self.optimal_batch_size = current_size

        logger.debug(
            f"Optimized batch size: {self.optimal_batch_size} "
            f"(throughput: {throughput:.2f} obj/s, error rate: {error_rate:.2%})"
        )
