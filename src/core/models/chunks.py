"""Core chunk models.

This module defines the core models for representing document chunks and
their metadata. It provides dataclasses for chunks and chunk-level metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from src.ml.processing.models.chunks import ProcessedChunk

    from .references import Reference


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""

    content_type: str  # Type of content (text, code, etc.)
    language: str | None = None  # Content language
    source_file: str | None = None  # Original file path
    line_numbers: tuple[int, int] | None = None  # Start and end line numbers
    custom_metadata: dict[str, Any] = field(default_factory=dict)  # Additional metadata


@dataclass
class Chunk:
    """Represents a document chunk.

    This class represents the core chunk model without ML-specific features.
    ML processing results are stored in the corresponding ProcessedChunk
    model in the ML package.
    """

    content: str  # Chunk content
    metadata: ChunkMetadata  # Chunk metadata
    id: UUID = field(default_factory=uuid4)  # Unique chunk identifier
    references: list[Reference] = field(default_factory=list)  # References to other chunks
    ml_processed: ProcessedChunk | None = field(default=None)  # Link to ML processing results
