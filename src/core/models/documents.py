"""Core document models.

This module defines the core models for representing documents and their
metadata. It provides dataclasses for documents, document metadata, and
document relationships.
"""

# Standard library imports
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4

# Local imports
from src.core.models.chunks import Chunk


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
    source_path: Optional[str] = None  # Original file path
    mime_type: Optional[str] = None  # MIME type
    encoding: Optional[str] = None  # Character encoding
    language: Optional[str] = None  # Document language
    custom_metadata: Dict = field(default_factory=dict)  # Additional metadata


@dataclass
class Document:
    """Represents a document in the system."""

    id: UUID = field(default_factory=uuid4)  # Unique document identifier
    metadata: DocumentMetadata  # Document metadata
    chunks: List[Chunk] = field(default_factory=list)  # Document chunks
    status: DocumentStatus = DocumentStatus.PENDING  # Processing status
    parent_id: Optional[UUID] = None  # Parent document ID
    child_ids: Set[UUID] = field(default_factory=set)  # Child document IDs
    error_message: Optional[str] = None  # Error message if processing failed


@dataclass
class ProcessingStep:
    """Represents a document processing step."""

    step_name: str  # Name of the processing step
    status: DocumentStatus  # Step status
    started_at: datetime = field(default_factory=datetime.utcnow)  # Start timestamp
    completed_at: Optional[datetime] = None  # Completion timestamp
    error_message: Optional[str] = None  # Error message if step failed
    metrics: Dict = field(default_factory=dict)  # Step metrics
