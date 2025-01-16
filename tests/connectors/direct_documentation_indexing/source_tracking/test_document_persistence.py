"""Tests for document persistence and storage functionality."""

from datetime import UTC, datetime, timedelta

from src.connectors.direct_documentation_indexing.source_tracking import add_document
from src.connectors.direct_documentation_indexing.source_tracking.storage import LineageStorage


def test_document_persistence(temp_lineage_dir):
    """Test persistence of document data across storage instances."""
    # Create first storage instance and add document
    storage1 = LineageStorage(str(temp_lineage_dir))
    doc_id = "test_doc"
    metadata = {"type": "pdf", "pages": 10}
    add_document(storage1, doc_id=doc_id, metadata=metadata)

    # Create new storage instance and verify data
    storage2 = LineageStorage(str(temp_lineage_dir))
    lineage = storage2.get_lineage(doc_id)
    assert lineage is not None, "Document should persist across storage instances"
    assert lineage.doc_id == doc_id, "Document ID should persist"
    assert lineage.metadata == metadata, "Metadata should persist"


def test_document_timestamps(storage):
    """Test document timestamp management."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)

    lineage = storage.get_lineage(doc_id)
    now = datetime.now(UTC)

    assert now - lineage.created_at < timedelta(seconds=1), "Created timestamp should be recent"
    assert now - lineage.last_modified < timedelta(seconds=1), "Modified timestamp should be recent"
    assert lineage.created_at == lineage.last_modified, "Initial timestamps should match"


def test_document_storage_isolation(temp_lineage_dir):
    """Test isolation between different storage instances."""
    storage1 = LineageStorage(str(temp_lineage_dir))
    storage2 = LineageStorage(str(temp_lineage_dir / "other"))

    # Add document to first storage
    doc_id = "test_doc"
    add_document(storage1, doc_id=doc_id)

    # Verify document only exists in first storage
    assert storage1.get_lineage(doc_id) is not None, "Document should exist in first storage"
    assert storage2.get_lineage(doc_id) is None, "Document should not exist in second storage"


def test_storage_path_creation(tmp_path):
    """Test automatic creation of storage directory."""
    storage_path = tmp_path / "nonexistent" / "lineage"
    storage = LineageStorage(str(storage_path))

    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)

    assert storage_path.exists(), "Storage directory should be created"
    assert storage.get_lineage(doc_id) is not None, "Document should be stored"
