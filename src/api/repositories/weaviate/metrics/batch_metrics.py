"""Batch operation metrics tracking."""

from collections import Counter
import logging
from typing import Dict

from .base import BaseMetrics, MetricCollector

logger = logging.getLogger(__name__)


class BatchMetrics(BaseMetrics, MetricCollector):
    """Tracks metrics for batch operations."""

    def __init__(self):
        """Initialize batch metrics."""
        super().__init__()
        self.total_batches = 0
        self.successful_batches = 0
        self.failed_batches = 0
        self.total_objects = 0
        self.successful_objects = 0
        self.failed_objects = 0
        self.error_types = Counter()

    def record_success(self) -> None:
        """Record a successful operation."""
        self.record_object_success()

    def record_error(self, error_type: str = "unknown") -> None:
        """Record an error."""
        self.record_object_error(error_type)

    def record_batch_completion(self) -> None:
        """Record successful batch completion."""
        self.total_batches += 1
        self.successful_batches += 1
        self.notify_observers("batch_success_rate", self.successful_batches / self.total_batches)

    def record_batch_error(self, error_type: str) -> None:
        """Record batch error.

        Args:
            error_type: Type of error that occurred
        """
        self.total_batches += 1
        self.failed_batches += 1
        self.error_types[error_type] += 1
        self.notify_observers("batch_error_rate", self.failed_batches / self.total_batches)

    def record_object_success(self, count: int = 1) -> None:
        """Record successful object processing.

        Args:
            count: Number of successful objects
        """
        self.total_objects += count
        self.successful_objects += count
        self.notify_observers("object_success_rate", self.successful_objects / self.total_objects)

    def record_object_error(self, error_type: str, count: int = 1) -> None:
        """Record object processing error.

        Args:
            error_type: Type of error that occurred
            count: Number of failed objects
        """
        self.total_objects += count
        self.failed_objects += count
        self.error_types[error_type] += count
        self.notify_observers("object_error_rate", self.failed_objects / self.total_objects)

    def get_summary(self) -> Dict:
        """Get summary of batch operation metrics.

        Returns:
            Dictionary containing metrics summary
        """
        batch_success_rate = (
            (self.successful_batches / self.total_batches * 100) if self.total_batches > 0 else 0
        )
        object_success_rate = (
            (self.successful_objects / self.total_objects * 100) if self.total_objects > 0 else 0
        )

        return {
            "total_batches": self.total_batches,
            "successful_batches": self.successful_batches,
            "failed_batches": self.failed_batches,
            "batch_success_rate": round(batch_success_rate, 2),
            "total_objects": self.total_objects,
            "successful_objects": self.successful_objects,
            "failed_objects": self.failed_objects,
            "object_success_rate": round(object_success_rate, 2),
            "error_types": dict(self.error_types),
        }
