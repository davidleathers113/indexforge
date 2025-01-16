"""Core models.

This module defines the core data models for documents, chunks,
and references used throughout the application.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Enumeration of supported document types."""

    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    TEXT = "text"
    NOTION = "notion"


class DocumentStatus(str, Enum):
    """Enumeration of document processing statuses."""

    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class ProcessingStep(str, Enum):
    """Enumeration of document processing steps."""

    EXTRACTION = "extraction"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    REFERENCE_DETECTION = "reference_detection"


class DocumentMetadata(BaseModel):
    """Metadata for a document."""

    title: str
    author: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    mime_type: str | None = None
    size_bytes: int
    page_count: int | None = None
    language: str | None = None
    source_path: str | None = None
    custom_metadata: dict[str, str] = Field(default_factory=dict)


class Document(BaseModel):
    """Base document model."""

    id: UUID
    type: DocumentType
    status: DocumentStatus = Field(default=DocumentStatus.PENDING)
    metadata: DocumentMetadata
    content: str
    processing_history: list[ProcessingStep] = Field(default_factory=list)
    error_message: str | None = None


class ChunkMetadata(BaseModel):
    """Metadata for a document chunk."""

    document_id: UUID
    sequence_number: int
    start_offset: int
    end_offset: int
    page_number: int | None = None
    section_title: str | None = None
    custom_metadata: dict[str, str] = Field(default_factory=dict)


class Chunk(BaseModel):
    """Base chunk model."""

    id: UUID
    content: str
    metadata: ChunkMetadata
    embedding: list[float] | None = None


class ProcessedChunk(Chunk):
    """Processed chunk with additional attributes."""

    processed_content: str
    tokens: list[str] = Field(default_factory=list)
    named_entities: dict[str, str] = Field(default_factory=dict)
    sentiment_score: float | None = None
    importance_score: float | None = None


class ReferenceType(str, Enum):
    """Enumeration of reference types."""

    CITATION = "citation"
    SEMANTIC = "semantic"
    HYPERLINK = "hyperlink"
    FOOTNOTE = "footnote"


class Reference(BaseModel):
    """Base reference model."""

    source_id: UUID
    target_id: UUID
    type: ReferenceType
    confidence: float = Field(default=1.0)
    metadata: dict[str, str] = Field(default_factory=dict)


class CitationReference(Reference):
    """Citation reference with additional attributes."""

    citation_text: str
    page_number: int | None = None
    style: str | None = None


class SemanticReference(Reference):
    """Semantic reference with additional attributes."""

    similarity_score: float
    context_window: str | None = None
    embedding_model: str | None = None
