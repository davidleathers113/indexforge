"""Core reference models.

This module defines the core models for managing references between chunks
and documents. It provides enums for reference types and dataclasses for
representing references.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID


class ReferenceType(Enum):
    """Types of references between chunks."""

    # Direct references (explicit connections)
    CITATION = "citation"  # Direct quote or citation
    CONTINUATION = "continuation"  # Content continues in another chunk
    LINK = "link"  # Explicit link/reference to another chunk

    # Indirect references (semantic connections)
    RELATED = "related"  # Semantically related content
    SIMILAR = "similar"  # Similar topic or content
    CONTEXT = "context"  # Provides context or background

    # Structural references (document organization)
    PARENT = "parent"  # Parent section or container
    CHILD = "child"  # Child section or subsection
    NEXT = "next"  # Next sequential chunk
    PREVIOUS = "previous"  # Previous sequential chunk
    TOC = "toc"  # Table of contents entry


@dataclass
class Reference:
    """Represents a reference between two chunks."""

    source_id: UUID  # ID of the source chunk
    target_id: UUID  # ID of the target chunk
    ref_type: ReferenceType  # Type of reference
    metadata: dict = field(default_factory=dict)  # Additional reference metadata
    bidirectional: bool = False  # Whether reference is bidirectional


@dataclass
class CitationReference(Reference):
    """Represents a citation reference between chunks."""

    text: str = field(repr=True)  # The cited text
    start_pos: int = field(repr=True)  # Start position in source chunk
    end_pos: int = field(repr=True)  # End position in source chunk


@dataclass
class SemanticReference(Reference):
    """Represents a semantic reference between chunks."""

    similarity_score: float = field(repr=True)  # Similarity score between chunks
    topic_id: int | None = None  # Optional topic cluster ID
