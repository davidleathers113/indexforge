"""
Document transformation tracking.

This module provides the Transformation model for tracking changes made to documents,
including content modifications, metadata updates, and structural changes.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.core.tracking.enums import TransformationType


@dataclass
class Transformation:
    """
    Represents a transformation applied to a document.

    This class records changes made to a document's content or structure,
    tracking the type of transformation, when it occurred, and relevant parameters.

    Attributes:
        transform_type: Type of transformation applied
        timestamp: When the transformation occurred (UTC)
        description: Human-readable description of the change
        parameters: Parameters used in the transformation
        metadata: Additional metadata about the transformation

    Example:
        ```python
        transform = Transformation(
            transform_type=TransformationType.CONTENT,
            description="Converted to plain text",
            parameters={"format": "txt", "encoding": "utf-8"},
            metadata={"transformer_version": "2.0.0"}
        )
        ```
    """

    transform_type: TransformationType
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    description: str = ""
    parameters: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the transformation to a dictionary."""
        return {
            "transform_type": self.transform_type.value,  # Convert enum to string
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "parameters": self.parameters,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transformation":
        """Create a Transformation instance from a dictionary."""
        data = data.copy()  # Create a copy to avoid modifying the input
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if isinstance(data.get("transform_type"), str):
            data["transform_type"] = TransformationType(data["transform_type"])
        return cls(**data)
