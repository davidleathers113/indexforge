"""Tests for document storage functionality."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from src.core.models.documents import Document, DocumentMetadata, DocumentStatus, DocumentType
from src.core.tracking.storage import DocumentStorage


@pytest.fixture
def storage_path(tmp_path: Path) -> Path:
    """Provide temporary storage path."""
    return tmp_path / "test_storage"


@pytest.fixture
def storage(storage_path: Path) -> DocumentStorage:
    """Provide document storage instance."""
    return DocumentStorage(storage_path)


@pytest.fixture
def sample_document() -> Document:
    """Provide a sample document for testing."""
    metadata = DocumentMetadata(
        title="Test Document",
        doc_type=DocumentType.TEXT,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        source_path="/path/to/test.txt",
        mime_type="text/plain",
        encoding="utf-8",
        language="en",
        custom_metadata={"key": "value"},
    )
    return Document(metadata=metadata, id=uuid4(), status=DocumentStatus.PENDING)


def test_storage_initialization(storage_path: Path):
    """Test storage initialization creates directory."""
    storage = DocumentStorage(storage_path)
    assert storage_path.exists()
    assert storage_path.is_dir()
    assert len(storage.documents) == 0


def test_save_and_get_document(storage: DocumentStorage, sample_document: Document):
    """Test saving and retrieving a document."""
    storage.save_document(sample_document)
    retrieved = storage.get_document(sample_document.id)
    assert retrieved is not None
    assert retrieved.id == sample_document.id
    assert retrieved.metadata.title == sample_document.metadata.title
    assert retrieved.metadata.doc_type == sample_document.metadata.doc_type
    assert retrieved.status == sample_document.status


def test_delete_document(storage: DocumentStorage, sample_document: Document):
    """Test deleting a document."""
    storage.save_document(sample_document)
    storage.delete_document(sample_document.id)
    assert storage.get_document(sample_document.id) is None


def test_delete_nonexistent_document(storage: DocumentStorage):
    """Test deleting a nonexistent document raises KeyError."""
    with pytest.raises(KeyError):
        storage.delete_document(uuid4())


def test_save_invalid_document_type(storage: DocumentStorage, sample_document: Document):
    """Test saving a document with invalid type raises ValueError."""
    sample_document.metadata.doc_type = "invalid_type"  # type: ignore
    with pytest.raises(ValueError):
        storage.save_document(sample_document)


def test_document_persistence(storage_path: Path, sample_document: Document):
    """Test document persistence across storage instances."""
    # Save document
    storage1 = DocumentStorage(storage_path)
    storage1.save_document(sample_document)

    # Load in new instance
    storage2 = DocumentStorage(storage_path)
    retrieved = storage2.get_document(sample_document.id)
    assert retrieved is not None
    assert retrieved.id == sample_document.id
    assert retrieved.metadata.title == sample_document.metadata.title


def test_document_relationships(storage: DocumentStorage):
    """Test document parent-child relationships."""
    # Create parent
    parent_metadata = DocumentMetadata(
        title="Parent Document",
        doc_type=DocumentType.PDF,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    parent = Document(metadata=parent_metadata, id=uuid4())
    storage.save_document(parent)

    # Create child
    child_metadata = DocumentMetadata(
        title="Child Document",
        doc_type=DocumentType.TEXT,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    child = Document(metadata=child_metadata, id=uuid4(), parent_id=parent.id)
    storage.save_document(child)

    # Update parent
    parent.child_ids.add(child.id)
    storage.save_document(parent)

    # Verify relationships
    retrieved_parent = storage.get_document(parent.id)
    retrieved_child = storage.get_document(child.id)
    assert retrieved_parent is not None
    assert retrieved_child is not None
    assert child.id in retrieved_parent.child_ids
    assert retrieved_child.parent_id == parent.id


def test_storage_file_format(
    storage: DocumentStorage, sample_document: Document, storage_path: Path
):
    """Test storage file format and content."""
    storage.save_document(sample_document)
    data_file = storage_path / "documents.json"
    assert data_file.exists()

    # Verify JSON structure
    data = json.loads(data_file.read_text())
    doc_data = data[str(sample_document.id)]
    assert doc_data["id"] == str(sample_document.id)
    assert doc_data["metadata"]["title"] == sample_document.metadata.title
    assert doc_data["metadata"]["doc_type"] == sample_document.metadata.doc_type.value
    assert doc_data["status"] == sample_document.status.value
