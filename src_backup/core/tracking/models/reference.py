"""
Document chunk reference tracking.

This module provides the ChunkReference model for tracking relationships between
different chunks of content, including similarity scores and topic associations.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.core.tracking.enums import ReferenceType


@dataclass
class ChunkReference:
    """
    Represents a reference between two document chunks.

    This class tracks relationships between different chunks of content,
    including similarity scores and topic associations.

    Attributes:
        source_id: ID of the source chunk
        target_id: ID of the target chunk
        ref_type: Type of reference relationship
        similarity_score: Optional similarity measure (0-1)
        topic_id: Optional ID of shared topic
        created_at: When the reference was created (UTC)
        metadata: Additional reference metadata

    Example:
        ```python
        ref = ChunkReference(
            source_id="chunk123",
            target_id="chunk456",
            ref_type=ReferenceType.SEMANTIC,
            similarity_score=0.85,
            topic_id=42,
            metadata={"method": "cosine_similarity"}
        )
        ```
    """

    source_id: str
    target_id: str
    ref_type: ReferenceType
    similarity_score: float | None = None
    topic_id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the chunk reference to a dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "ref_type": self.ref_type.value,  # Convert enum to string
            "similarity_score": self.similarity_score,
            "topic_id": self.topic_id,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChunkReference":
        """Create a ChunkReference instance from a dictionary."""
        data = data.copy()  # Create a copy to avoid modifying the input
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("ref_type"), str):
            data["ref_type"] = ReferenceType(data["ref_type"])
        return cls(**data)
