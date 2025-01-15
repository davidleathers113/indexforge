"""Core chunk models.

This module defines the core models for representing document chunks and
their metadata. It provides dataclasses for chunks, embeddings, and
chunk-level metadata.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import UUID, uuid4

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from src.core.models.references import Reference


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""

    content_type: str  # Type of content (text, code, etc.)
    language: Optional[str] = None  # Content language
    source_file: Optional[str] = None  # Original file path
    line_numbers: Optional[tuple[int, int]] = None  # Start and end line numbers
    custom_metadata: Dict = field(default_factory=dict)  # Additional metadata


@dataclass
class Chunk:
    """Represents a document chunk."""

    id: UUID = field(default_factory=uuid4)  # Unique chunk identifier
    content: str  # Chunk content
    metadata: ChunkMetadata  # Chunk metadata
    references: List[Reference] = field(default_factory=list)  # References to other chunks
    embedding: Optional[np.ndarray] = None  # Vector embedding of content


@dataclass
class ProcessedChunk(Chunk):
    """Represents a processed document chunk with additional attributes."""

    tokens: List[str]  # Tokenized content
    named_entities: List[Dict]  # Named entities found in content
    sentiment_score: Optional[float] = None  # Content sentiment score
    topic_id: Optional[int] = None  # Assigned topic cluster ID
