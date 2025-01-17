"""Processing step models and data structures.

This module provides the core models for tracking document processing steps,
including status tracking and performance metrics.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, Optional


class ProcessingStatus(Enum):
    """Status of a document processing step."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProcessingStep:
    """Represents a single step in document processing.

    This class tracks the execution and outcome of a processing operation,
    including performance metrics and error details.

    Attributes:
        step_name: Name of the processing step
        status: Current status of the step
        details: Step-specific details and results
        metadata: Additional context (metrics, errors)
        timestamp: When the step was executed

    Example:
        ```python
        step = ProcessingStep(
            step_name="text_extraction",
            status=ProcessingStatus.SUCCESS,
            details={"chars": 5000, "pages": 10},
            metadata={
                "metrics": {"duration_ms": 1500},
                "error_message": None
            }
        )
        ```
    """

    def __init__(
        self,
        step_name: str,
        status: ProcessingStatus,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Initialize a processing step.

        Args:
            step_name: Name of the processing step
            status: Current status of the step
            details: Step-specific details and results
            metadata: Additional context (metrics, errors)
            timestamp: When the step was executed (defaults to current UTC time)
        """
        self.step_name = step_name
        self.status = status
        self.details = details or {}
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the processing step to a dictionary.

        Returns:
            Dictionary representation of the processing step
        """
        return {
            "step_name": self.step_name,
            "status": self.status.value,
            "details": self.details,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessingStep":
        """Create a ProcessingStep instance from a dictionary.

        Args:
            data: Dictionary containing processing step data

        Returns:
            New ProcessingStep instance

        Example:
            ```python
            data = {
                "step_name": "text_extraction",
                "status": "success",
                "details": {"chars": 5000},
                "metadata": {"duration_ms": 1500},
                "timestamp": datetime.now(UTC)
            }
            step = ProcessingStep.from_dict(data)
            ```
        """
        return cls(
            step_name=data["step_name"],
            status=ProcessingStatus(data["status"]),
            details=data.get("details", {}),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp"),
        )

    @property
    def duration_ms(self) -> Optional[int]:
        """Get the step duration in milliseconds if available.

        Returns:
            Duration in milliseconds or None if not available
        """
        metrics = self.metadata.get("metrics", {})
        return metrics.get("duration_ms")

    @property
    def error_message(self) -> Optional[str]:
        """Get the error message if any.

        Returns:
            Error message or None if no error occurred
        """
        return self.metadata.get("error_message")

    def is_terminal_state(self) -> bool:
        """Check if the step is in a terminal state.

        Returns:
            True if the step has completed (success/error/failed/skipped)
        """
        return self.status in {
            ProcessingStatus.SUCCESS,
            ProcessingStatus.ERROR,
            ProcessingStatus.FAILED,
            ProcessingStatus.SKIPPED,
        }

    def is_error_state(self) -> bool:
        """Check if the step is in an error state.

        Returns:
            True if the step resulted in an error or failure
        """
        return self.status in {ProcessingStatus.ERROR, ProcessingStatus.FAILED}
