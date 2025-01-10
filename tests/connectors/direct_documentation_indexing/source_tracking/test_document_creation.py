"""Tests for basic document creation and validation."""

import pytest

from src.connectors.direct_documentation_indexing.source_tracking import add_document


def test_add_document(storage):
    """Test adding a document to lineage tracking."""
    doc_id = "test_doc"
    metadata = {"type": "pdf", "pages": 10}
    add_document(storage, doc_id=doc_id, metadata=metadata)

    lineage = storage.get_lineage(doc_id)
    assert lineage is not None, "Document should be created"
    assert lineage.doc_id == doc_id, "Document ID should match"
    assert lineage.metadata == metadata, "Metadata should be preserved"


def test_add_document_with_origin(storage):
    """Test adding a document with origin information."""
    doc_id = "test_doc"
    origin_id = "source_123"
    origin_source = "external_system"
    origin_type = "pdf"

    add_document(
        storage,
        doc_id=doc_id,
        origin_id=origin_id,
        origin_source=origin_source,
        origin_type=origin_type,
    )

    lineage = storage.get_lineage(doc_id)
    assert lineage.origin_id == origin_id, "Origin ID should be preserved"
    assert lineage.origin_source == origin_source, "Origin source should be preserved"
    assert lineage.origin_type == origin_type, "Origin type should be preserved"


def test_add_document_duplicate(storage):
    """Test handling of duplicate document creation."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)

    with pytest.raises(ValueError, match=f"Document {doc_id} already exists"):
        add_document(storage, doc_id=doc_id)


def test_add_document_invalid_id(storage):
    """Test handling of invalid document IDs."""
    invalid_ids = ["", " ", None]
    for doc_id in invalid_ids:
        with pytest.raises(ValueError):
            add_document(storage, doc_id=doc_id)


def test_add_document_with_empty_metadata(storage):
    """Test adding a document with empty metadata."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)

    lineage = storage.get_lineage(doc_id)
    assert lineage.metadata == {}, "Empty metadata should be initialized as empty dict"
    assert lineage.created_at is not None, "Created timestamp should be set"
    assert lineage.last_modified is not None, "Modified timestamp should be set"
