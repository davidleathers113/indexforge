"""
Processing step tracking for document operations.

This module provides the ProcessingStep model for tracking individual processing
operations performed on documents, including status, timing, and metadata.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.core.tracking.enums import ProcessingStatus


@dataclass
class ProcessingStep:
    """
    Represents a processing step applied to a document.

    This class tracks individual processing operations performed on a document,
    including their status, timing, and any associated metadata.

    Attributes:
        step_name: Name of the processing step (e.g., "text_extraction")
        status: Current status of the step (success, error, etc.)
        timestamp: When the step was executed (UTC)
        details: Step-specific details like metrics or results
        metadata: Additional metadata about the step

    Example:
        ```python
        step = ProcessingStep(
            step_name="text_extraction",
            status=ProcessingStatus.SUCCESS,
            details={"chars": 5000, "pages": 10},
            metadata={"processor_version": "1.2.3"}
        )
        ```
    """

    step_name: str
    status: ProcessingStatus
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    details: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the processing step to a dictionary."""
        return {
            "step_name": self.step_name,
            "status": self.status.value,  # Convert enum to string
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProcessingStep":
        """Create a ProcessingStep instance from a dictionary."""
        data = data.copy()  # Create a copy to avoid modifying the input
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if isinstance(data.get("status"), str):
            data["status"] = ProcessingStatus(data["status"])
        return cls(**data)
