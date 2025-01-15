"""Metrics tracking for Weaviate operations."""

from dataclasses import dataclass, field
import logging
from statistics import mean, median
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BatchPerformanceMetrics:
    """Performance metrics for a single batch."""

    batch_size: int
    duration_seconds: float
    objects_per_second: float
    error_rate: float
    memory_usage_mb: Optional[float] = None


class BatchPerformanceTracker:
    """Tracks and analyzes batch performance for optimization."""

    def __init__(self, min_batch_size: int = 50, max_batch_size: int = 500, window_size: int = 10):
        """Initialize performance tracker.

        Args:
            min_batch_size: Minimum allowed batch size
            max_batch_size: Maximum allowed batch size
            window_size: Number of batches to analyze for optimization
        """
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.window_size = window_size
        self.metrics_history: List[BatchPerformanceMetrics] = []
        self.current_batch_start: Optional[float] = None
        self.optimal_batch_size: int = min_batch_size

    def start_batch(self, batch_size: int) -> None:
        """Start timing a new batch operation."""
        self.current_batch_start = time.time()
        self.current_batch_size = batch_size

    def end_batch(
        self, successful_objects: int, failed_objects: int, memory_usage_mb: Optional[float] = None
    ) -> None:
        """Record metrics for completed batch."""
        if self.current_batch_start is None:
            logger.warning("end_batch called without start_batch")
            return

        duration = time.time() - self.current_batch_start
        total_objects = successful_objects + failed_objects

        metrics = BatchPerformanceMetrics(
            batch_size=self.current_batch_size,
            duration_seconds=duration,
            objects_per_second=total_objects / duration if duration > 0 else 0,
            error_rate=failed_objects / total_objects if total_objects > 0 else 0,
            memory_usage_mb=memory_usage_mb,
        )

        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.window_size:
            self.metrics_history.pop(0)
            self._optimize_batch_size()

    def _optimize_batch_size(self) -> None:
        """Analyze recent performance and adjust optimal batch size."""
        if len(self.metrics_history) < self.window_size:
            return

        # Group metrics by batch size
        size_groups: Dict[int, List[BatchPerformanceMetrics]] = {}
        for metric in self.metrics_history:
            if metric.batch_size not in size_groups:
                size_groups[metric.batch_size] = []
            size_groups[metric.batch_size].append(metric)

        # Calculate average performance for each batch size
        size_performance = {}
        for size, metrics in size_groups.items():
            avg_throughput = mean(m.objects_per_second for m in metrics)
            avg_error_rate = mean(m.error_rate for m in metrics)

            # Penalize high error rates
            performance_score = avg_throughput * (1 - avg_error_rate * 2)
            size_performance[size] = performance_score

        # Find best performing batch size
        best_size = max(size_performance.items(), key=lambda x: x[1])[0]

        # Gradually adjust optimal size
        if best_size > self.optimal_batch_size:
            self.optimal_batch_size = min(
                self.optimal_batch_size + 50, min(best_size, self.max_batch_size)
            )
        else:
            self.optimal_batch_size = max(
                self.optimal_batch_size - 50, max(best_size, self.min_batch_size)
            )

    def get_optimal_batch_size(self) -> int:
        """Get the current optimal batch size."""
        return self.optimal_batch_size

    def get_performance_summary(self) -> Dict:
        """Get summary of recent performance metrics."""
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


@dataclass
class BatchMetrics:
    """Metrics for batch operations."""

    total_batches: int = 0
    successful_batches: int = 0
    failed_batches: int = 0
    total_objects: int = 0
    successful_objects: int = 0
    failed_objects: int = 0
    errors: Dict[str, int] = field(default_factory=dict)

    def record_batch_completion(self) -> None:
        """Record successful batch completion."""
        self.total_batches += 1
        self.successful_batches += 1

    def record_batch_error(self) -> None:
        """Record batch error."""
        self.total_batches += 1
        self.failed_batches += 1

    def record_object_success(self) -> None:
        """Record successful object operation."""
        self.total_objects += 1
        self.successful_objects += 1

    def record_object_error(self, error_type: str = "unknown") -> None:
        """Record object error.

        Args:
            error_type: Type of error that occurred
        """
        self.total_objects += 1
        self.failed_objects += 1
        self.errors[error_type] = self.errors.get(error_type, 0) + 1

    def get_summary(self) -> Dict:
        """Get metrics summary.

        Returns:
            Dictionary containing metrics summary
        """
        return {
            "batches": {
                "total": self.total_batches,
                "successful": self.successful_batches,
                "failed": self.failed_batches,
                "success_rate": (
                    self.successful_batches / self.total_batches if self.total_batches > 0 else 0
                ),
            },
            "objects": {
                "total": self.total_objects,
                "successful": self.successful_objects,
                "failed": self.failed_objects,
                "success_rate": (
                    self.successful_objects / self.total_objects if self.total_objects > 0 else 0
                ),
            },
            "errors": dict(self.errors),
        }
