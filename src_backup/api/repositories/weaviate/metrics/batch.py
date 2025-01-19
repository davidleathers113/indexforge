"""Basic batch operation metrics."""

from dataclasses import dataclass, field

from .base import BaseMetrics


@dataclass
class BatchMetrics(BaseMetrics):
    """Metrics for batch operations."""

    total_batches: int = 0
    successful_batches: int = 0
    failed_batches: int = 0
    total_objects: int = 0
    successful_objects: int = 0
    failed_objects: int = 0
    errors: dict[str, int] = field(default_factory=dict)

    def record_batch_completion(self) -> None:
        """Record successful batch completion."""
        self.total_batches += 1
        self.successful_batches += 1
        self.notify_observers("batch_success_rate", self.successful_batches / self.total_batches)

    def record_batch_error(self) -> None:
        """Record batch error."""
        self.total_batches += 1
        self.failed_batches += 1
        self.notify_observers("batch_error_rate", self.failed_batches / self.total_batches)

    def record_object_success(self) -> None:
        """Record successful object operation."""
        self.total_objects += 1
        self.successful_objects += 1
        self.notify_observers("object_success_rate", self.successful_objects / self.total_objects)

    def record_object_error(self, error_type: str = "unknown") -> None:
        """Record object error."""
        self.total_objects += 1
        self.failed_objects += 1
        self.errors[error_type] = self.errors.get(error_type, 0) + 1
        self.notify_observers("object_error_rate", self.failed_objects / self.total_objects)

    def get_summary(self) -> dict:
        """Get metrics summary."""
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
