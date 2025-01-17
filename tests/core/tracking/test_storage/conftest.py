"""Shared test fixtures and utilities for document storage tests."""

from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

import pytest

from src.core.models.documents import Document, DocumentMetadata, DocumentStatus, DocumentType
from src.core.models.settings import Settings
from src.core.tracking.storage import DocumentStorage


def create_test_document(
    title: str = "Test Document",
    doc_type: DocumentType = DocumentType.TEXT,
    parent_id: Optional[UUID] = None,
    status: DocumentStatus = DocumentStatus.PENDING,
    **metadata_kwargs,
) -> Document:
    """Create a test document with given parameters.

    Args:
        title: Document title
        doc_type: Document type
        parent_id: Optional parent document ID
        status: Document status
        **metadata_kwargs: Additional metadata fields
    """
    metadata = DocumentMetadata(
        title=title,
        doc_type=doc_type,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        source_path=metadata_kwargs.get("source_path", "/path/to/test.txt"),
        mime_type=metadata_kwargs.get("mime_type", "text/plain"),
        encoding=metadata_kwargs.get("encoding", "utf-8"),
        language=metadata_kwargs.get("language", "en"),
        custom_metadata=metadata_kwargs.get("custom_metadata", {"key": "value"}),
    )
    return Document(metadata=metadata, id=uuid4(), status=status, parent_id=parent_id)


@pytest.fixture
def storage_path(tmp_path: Path) -> Path:
    """Provide temporary storage path."""
    return tmp_path / "test_storage"


@pytest.fixture
def settings(storage_path: Path) -> Settings:
    """Provide test settings."""
    return Settings(storage_path=storage_path, max_metrics_history=5, metrics_enabled=True)


@pytest.fixture
def storage(settings: Settings) -> DocumentStorage:
    """Provide document storage instance."""
    return DocumentStorage(settings.storage_path, settings)


@pytest.fixture
def sample_document() -> Document:
    """Provide a sample document for testing."""
    return create_test_document()


@pytest.fixture
def document_with_parent(storage: DocumentStorage) -> Document:
    """Provide a document with a parent relationship."""
    parent = create_test_document(title="Parent Document", doc_type=DocumentType.PDF)
    storage.save_document(parent)

    child = create_test_document(
        title="Child Document", doc_type=DocumentType.TEXT, parent_id=parent.id
    )
    return child


@pytest.fixture
def document_chain(storage: DocumentStorage) -> list[UUID]:
    """Provide a chain of related documents."""
    doc_ids = []
    parent_id = None

    for i in range(3):
        doc = create_test_document(title=f"Document {i}", parent_id=parent_id)
        storage.save_document(doc)
        doc_ids.append(doc.id)
        parent_id = doc.id

    return doc_ids
