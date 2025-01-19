"""Test data builders for storage service tests.

This module provides builder classes for constructing test data objects
in a flexible and reusable way.
"""

from uuid import UUID

from src.core.models.chunks import Chunk, ChunkMetadata
from src.core.models.documents import Document, DocumentMetadata, DocumentType
from src.core.models.references import Reference


class DocumentBuilder:
    """Builder for test Document objects."""

    def __init__(self):
        """Initialize with default values."""
        self.title = "Test Document"
        self.source = "test"
        self.doc_type = DocumentType.TEXT
        self.content = "Test content"

    def with_title(self, title: str) -> "DocumentBuilder":
        """Set document title."""
        self.title = title
        return self

    def with_source(self, source: str) -> "DocumentBuilder":
        """Set document source."""
        self.source = source
        return self

    def with_type(self, doc_type: DocumentType) -> "DocumentBuilder":
        """Set document type."""
        self.doc_type = doc_type
        return self

    def with_content(self, content: str) -> "DocumentBuilder":
        """Set document content."""
        self.content = content
        return self

    def build(self) -> Document:
        """Create Document instance."""
        metadata = DocumentMetadata(
            title=self.title,
            source=self.source,
            doc_type=self.doc_type,
        )
        return Document(content=self.content, metadata=metadata)


class ChunkBuilder:
    """Builder for test Chunk objects."""

    def __init__(self):
        """Initialize with default values."""
        self.document_id: UUID | None = None
        self.start_index = 0
        self.end_index = 10
        self.content = "Test chunk content"

    def with_document_id(self, document_id: UUID) -> "ChunkBuilder":
        """Set chunk's document ID."""
        self.document_id = document_id
        return self

    def with_indices(self, start: int, end: int) -> "ChunkBuilder":
        """Set chunk's start and end indices."""
        self.start_index = start
        self.end_index = end
        return self

    def with_content(self, content: str) -> "ChunkBuilder":
        """Set chunk content."""
        self.content = content
        return self

    def build(self) -> Chunk:
        """Create Chunk instance."""
        if self.document_id is None:
            raise ValueError("document_id must be set")

        metadata = ChunkMetadata(
            document_id=self.document_id,
            start_index=self.start_index,
            end_index=self.end_index,
        )
        return Chunk(content=self.content, metadata=metadata)


class ReferenceBuilder:
    """Builder for test Reference objects."""

    def __init__(self):
        """Initialize with default values."""
        self.source_id: UUID | None = None
        self.target_id: UUID | None = None
        self.reference_type = "cites"
        self.confidence = 0.95

    def with_source(self, source_id: UUID) -> "ReferenceBuilder":
        """Set reference source ID."""
        self.source_id = source_id
        return self

    def with_target(self, target_id: UUID) -> "ReferenceBuilder":
        """Set reference target ID."""
        self.target_id = target_id
        return self

    def with_type(self, reference_type: str) -> "ReferenceBuilder":
        """Set reference type."""
        self.reference_type = reference_type
        return self

    def with_confidence(self, confidence: float) -> "ReferenceBuilder":
        """Set reference confidence."""
        self.confidence = confidence
        return self

    def build(self) -> Reference:
        """Create Reference instance."""
        if self.source_id is None or self.target_id is None:
            raise ValueError("source_id and target_id must be set")

        return Reference(
            source_id=self.source_id,
            target_id=self.target_id,
            reference_type=self.reference_type,
            confidence=self.confidence,
        )
