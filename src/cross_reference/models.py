"""
Data models for cross-reference management.

This module defines the core data structures used for managing references
between document chunks, including enums for reference types and the
ChunkReference class for storing reference metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional


class ReferenceType(Enum):
    """
    Types of references between document chunks.

    This enum defines the different types of relationships that can exist
    between document chunks, enabling various types of navigation and
    analysis.

    Attributes:
        SEQUENTIAL: Next/previous chunks in document order
        SEMANTIC: References based on content similarity
        TOPIC: Chunks belonging to the same topic cluster
        CITATION: Direct citations or quotes between chunks
    """

    SEQUENTIAL = "sequential"  # Next/previous in sequence
    SEMANTIC = "semantic"  # Content similarity
    TOPIC = "topic"  # Same topic cluster
    CITATION = "citation"  # Direct citation/quote


@dataclass
class ChunkReference:
    """
    Represents a reference between two document chunks.

    This class encapsulates the relationship between two document chunks,
    including the type of reference, similarity scores, and associated
    metadata.

    Attributes:
        source_id (str): ID of the source chunk
        target_id (str): ID of the target chunk
        ref_type (ReferenceType): Type of reference
        similarity_score (Optional[float]): Similarity score (0-1)
        topic_id (Optional[int]): ID of shared topic cluster
        created_at (datetime): When the reference was created
        metadata (Dict): Additional reference metadata
    """

    source_id: str
    target_id: str
    ref_type: ReferenceType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    similarity_score: Optional[float] = None
    topic_id: Optional[int] = None

    @property
    def metadata(self) -> Dict:
        """Get reference metadata."""
        meta = {
            "timestamp": self.timestamp.isoformat(),
            "type": self.ref_type.value,
        }
        if self.similarity_score is not None:
            meta["similarity"] = self.similarity_score
        if self.topic_id is not None:
            meta["topic_id"] = self.topic_id
        return meta
