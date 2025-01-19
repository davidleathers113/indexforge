"""Core chunk models.

This module defines the core models for representing document chunks and
their metadata. It provides dataclasses for chunks, embeddings, and
chunk-level metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID, uuid4


try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

if TYPE_CHECKING:
    from .references import Reference


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""

    content_type: str  # Type of content (text, code, etc.)
    language: str | None = None  # Content language
    source_file: str | None = None  # Original file path
    line_numbers: tuple[int, int] | None = None  # Start and end line numbers
    custom_metadata: dict = field(default_factory=dict)  # Additional metadata


@dataclass
class Chunk:
    """Represents a document chunk."""

    content: str  # Chunk content
    metadata: ChunkMetadata  # Chunk metadata
    id: UUID = field(default_factory=uuid4)  # Unique chunk identifier
    references: list[Reference] = field(default_factory=list)  # References to other chunks
    embedding: np.ndarray | None = None  # Vector embedding of content


@dataclass
class ProcessedChunk(Chunk):
    """Represents a processed document chunk with additional attributes."""

    tokens: list[str] = field(default_factory=list)  # Tokenized content
    named_entities: list[dict] = field(default_factory=list)  # Named entities found in content
    sentiment_score: float | None = None  # Content sentiment score
    topic_id: int | None = None  # Assigned topic cluster ID
