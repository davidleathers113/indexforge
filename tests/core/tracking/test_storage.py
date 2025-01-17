"""Tests for document storage functionality."""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from src.core.models.documents import Document, DocumentMetadata, DocumentStatus, DocumentType
from src.core.models.settings import Settings
from src.core.tracking.storage import DocumentStorage


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Provide test settings."""
    return Settings(
        storage_path=tmp_path / "test_storage", max_metrics_history=5, metrics_enabled=True
    )


@pytest.fixture
def storage(settings: Settings) -> DocumentStorage:
    """Provide document storage instance."""
    return DocumentStorage(settings.storage_path, settings)


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


def test_storage_initialization(storage_path: Path, settings: Settings):
    """Test storage initialization creates directory."""
    storage = DocumentStorage(storage_path, settings)
    assert storage_path.exists()
    assert storage_path.is_dir()
    assert len(storage.documents) == 0
    assert storage.metrics is not None


def test_save_and_get_document(storage: DocumentStorage, sample_document: Document):
    """Test saving and retrieving a document."""
    storage.save_document(sample_document)
    retrieved = storage.get_document(sample_document.id)
    assert retrieved is not None
    assert retrieved.id == sample_document.id
    assert retrieved.metadata.title == sample_document.metadata.title
    assert retrieved.metadata.doc_type == sample_document.metadata.doc_type
    assert retrieved.status == sample_document.status

    # Verify metrics were collected
    metrics = storage.metrics.get_metrics()
    assert "save_document" in metrics
    assert "get_document" in metrics
    assert len(metrics["save_document"]) == 1
    assert len(metrics["get_document"]) == 1


def test_delete_document(storage: DocumentStorage, sample_document: Document):
    """Test deleting a document."""
    storage.save_document(sample_document)
    storage.delete_document(sample_document.id)
    assert storage.get_document(sample_document.id) is None

    # Verify metrics were collected
    metrics = storage.metrics.get_metrics()
    assert "delete_document" in metrics
    assert len(metrics["delete_document"]) == 1


def test_delete_nonexistent_document(storage: DocumentStorage):
    """Test deleting a nonexistent document raises KeyError."""
    with pytest.raises(KeyError):
        storage.delete_document(uuid4())

    # Verify metrics were collected even for failed operation
    metrics = storage.metrics.get_metrics()
    assert "delete_document" in metrics
    assert len(metrics["delete_document"]) == 1


def test_save_invalid_document_type(storage: DocumentStorage, sample_document: Document):
    """Test saving a document with invalid type raises ValueError."""
    sample_document.metadata.doc_type = "invalid_type"  # type: ignore
    with pytest.raises(ValueError):
        storage.save_document(sample_document)

    # Verify metrics were collected even for failed operation
    metrics = storage.metrics.get_metrics()
    assert "save_document" in metrics
    assert len(metrics["save_document"]) == 1


def test_document_persistence(storage_path: Path, settings: Settings, sample_document: Document):
    """Test document persistence across storage instances."""
    # Save document
    storage1 = DocumentStorage(storage_path, settings)
    storage1.save_document(sample_document)

    # Verify first storage metrics
    metrics1 = storage1.metrics.get_metrics()
    assert "save_document" in metrics1
    assert len(metrics1["save_document"]) == 1

    # Load in new instance
    storage2 = DocumentStorage(storage_path, settings)
    retrieved = storage2.get_document(sample_document.id)
    assert retrieved is not None
    assert retrieved.id == sample_document.id
    assert retrieved.metadata.title == sample_document.metadata.title

    # Verify second storage metrics
    metrics2 = storage2.metrics.get_metrics()
    assert "load_data" in metrics2
    assert "get_document" in metrics2


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

    # Verify metrics for relationship operations
    metrics = storage.metrics.get_metrics()
    assert len(metrics["save_document"]) == 3  # Initial save + child save + parent update
    assert len(metrics["get_document"]) == 2  # Parent and child retrieval


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

    # Verify metrics for save operation
    metrics = storage.metrics.get_metrics()
    assert "save_document" in metrics
    assert len(metrics["save_document"]) == 1


def test_metrics_disabled(storage_path: Path):
    """Test storage works correctly with metrics disabled."""
    settings = Settings(storage_path=storage_path, metrics_enabled=False)
    storage = DocumentStorage(storage_path, settings)
    assert storage.metrics is None

    # Operations should work without metrics
    doc = Document(
        metadata=DocumentMetadata(
            title="Test",
            doc_type=DocumentType.TEXT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
        id=uuid4(),
    )
    storage.save_document(doc)
    retrieved = storage.get_document(doc.id)
    assert retrieved is not None
    assert retrieved.id == doc.id


def test_update_document_metadata(storage: DocumentStorage, sample_document: Document):
    """Test updating document metadata."""
    storage.save_document(sample_document)
    original_updated_at = sample_document.metadata.updated_at

    # Wait to ensure timestamp difference
    time.sleep(0.1)

    updates = {
        "metadata": {
            "title": "Updated Title",
            "language": "fr",
            "custom_metadata": {"new_key": "new_value"},
        }
    }
    storage.update_document(sample_document.id, updates)

    # Verify updates
    updated_doc = storage.get_document(sample_document.id)
    assert updated_doc is not None
    assert updated_doc.metadata.title == "Updated Title"
    assert updated_doc.metadata.language == "fr"
    assert updated_doc.metadata.custom_metadata == {"new_key": "new_value"}
    assert updated_doc.metadata.updated_at > original_updated_at

    # Verify metrics
    metrics = storage.metrics.get_metrics()
    assert "update_document" in metrics
    assert len(metrics["update_document"]) == 1


def test_update_document_status(storage: DocumentStorage, sample_document: Document):
    """Test updating document status."""
    storage.save_document(sample_document)

    updates = {"status": DocumentStatus.PROCESSED}
    storage.update_document(sample_document.id, updates)

    updated_doc = storage.get_document(sample_document.id)
    assert updated_doc is not None
    assert updated_doc.status == DocumentStatus.PROCESSED


def test_update_nonexistent_document(storage: DocumentStorage):
    """Test updating nonexistent document raises error."""
    with pytest.raises(KeyError):
        storage.update_document(uuid4(), {"status": DocumentStatus.PROCESSED})


def test_update_invalid_document_type(storage: DocumentStorage, sample_document: Document):
    """Test updating to invalid document type raises error."""
    storage.save_document(sample_document)

    with pytest.raises(ValueError):
        storage.update_document(
            sample_document.id, {"metadata": {"doc_type": "invalid_type"}}  # type: ignore
        )


def test_update_document_relationships(storage: DocumentStorage):
    """Test updating document relationships."""
    # Create parent and child documents
    parent = Document(
        metadata=DocumentMetadata(
            title="Parent",
            doc_type=DocumentType.PDF,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
        id=uuid4(),
    )
    child = Document(
        metadata=DocumentMetadata(
            title="Child",
            doc_type=DocumentType.TEXT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
        id=uuid4(),
    )

    storage.save_document(parent)
    storage.save_document(child)

    # Update relationships
    storage.update_document(child.id, {"parent_id": parent.id})

    # Verify updates
    updated_parent = storage.get_document(parent.id)
    updated_child = storage.get_document(child.id)
    assert updated_parent is not None
    assert updated_child is not None
    assert child.id in updated_parent.child_ids
    assert updated_child.parent_id == parent.id


def test_update_document_error_message(storage: DocumentStorage, sample_document: Document):
    """Test updating document error message."""
    storage.save_document(sample_document)

    error_msg = "Test error message"
    storage.update_document(sample_document.id, {"error_message": error_msg})

    updated_doc = storage.get_document(sample_document.id)
    assert updated_doc is not None
    assert updated_doc.error_message == error_msg


def test_update_multiple_fields(storage: DocumentStorage, sample_document: Document):
    """Test updating multiple document fields at once."""
    storage.save_document(sample_document)

    updates = {
        "metadata": {"title": "New Title"},
        "status": DocumentStatus.PROCESSED,
        "error_message": "Test error",
    }
    storage.update_document(sample_document.id, updates)

    updated_doc = storage.get_document(sample_document.id)
    assert updated_doc is not None
    assert updated_doc.metadata.title == "New Title"
    assert updated_doc.status == DocumentStatus.PROCESSED
    assert updated_doc.error_message == "Test error"


def test_update_invalid_status(storage: DocumentStorage, sample_document: Document):
    """Test updating to invalid status raises error."""
    storage.save_document(sample_document)

    with pytest.raises(ValueError):
        storage.update_document(sample_document.id, {"status": "invalid_status"})  # type: ignore


def test_update_nonexistent_parent(storage: DocumentStorage, sample_document: Document):
    """Test updating to nonexistent parent raises error."""
    storage.save_document(sample_document)

    with pytest.raises(ValueError):
        storage.update_document(sample_document.id, {"parent_id": uuid4()})


def test_update_nonexistent_children(storage: DocumentStorage, sample_document: Document):
    """Test updating to nonexistent children raises error."""
    storage.save_document(sample_document)

    with pytest.raises(ValueError):
        storage.update_document(sample_document.id, {"child_ids": [uuid4()]})
