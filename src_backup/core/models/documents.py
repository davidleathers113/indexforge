"""Core document models.

This module defines the core models for representing documents and their
metadata. It provides dataclasses for documents, document metadata, and
document relationships.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4


if TYPE_CHECKING:
    from .chunks import Chunk


class DocumentStatus(Enum):
    """Document processing status."""

    PENDING = "pending"  # Not yet processed
    PROCESSING = "processing"  # Currently being processed
    PROCESSED = "processed"  # Successfully processed
    FAILED = "failed"  # Processing failed
    ARCHIVED = "archived"  # Document archived


class DocumentType(Enum):
    """Types of documents that can be processed."""

    TEXT = "text"  # Plain text documents
    MARKDOWN = "markdown"  # Markdown documents
    HTML = "html"  # HTML documents
    PDF = "pdf"  # PDF documents
    CODE = "code"  # Source code files
    NOTION = "notion"  # Notion workspace exports


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
