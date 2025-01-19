"""Core document models.

This module defines the core models for representing documents and their
metadata. It provides dataclasses for documents, document metadata, and
document relationships.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from .types import DocumentStatus, DocumentType


if TYPE_CHECKING:
    from .chunks import Chunk


@dataclass
class DocumentMetadata:
    """Metadata for a document."""

    title: str  # Document title
    doc_type: DocumentType  # Document type
    created_at: datetime = field(default_factory=datetime.utcnow)  # Creation timestamp
    updated_at: datetime = field(default_factory=datetime.utcnow)  # Last update timestamp
    source_path: str | None = None  # Original file path
    mime_type: str | None = None  # MIME type
    encoding: str | None = None  # Character encoding
    language: str | None = None  # Document language
    custom_metadata: dict = field(default_factory=dict)  # Additional metadata


@dataclass
class Document:
    """Represents a document in the system."""

    metadata: DocumentMetadata  # Document metadata
    id: UUID = field(default_factory=uuid4)  # Unique document identifier
    chunks: list[Chunk] = field(default_factory=list)  # Document chunks
    status: DocumentStatus = field(default=DocumentStatus.PENDING)  # Processing status
    parent_id: UUID | None = None  # Parent document ID
    child_ids: set[UUID] = field(default_factory=set)  # Child document IDs
    error_message: str | None = None  # Error message if processing failed


@dataclass
class ProcessingStep:
    """Represents a document processing step."""

    step_name: str  # Name of the processing step
    status: DocumentStatus  # Step status
    started_at: datetime = field(default_factory=datetime.utcnow)  # Start timestamp
    completed_at: datetime | None = None  # Completion timestamp
    error_message: str | None = None  # Error message if step failed
    metrics: dict = field(default_factory=dict)  # Step metrics
