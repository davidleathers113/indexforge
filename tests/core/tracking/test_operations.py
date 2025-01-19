"""Tests for document operations functionality."""

import pytest

from src.core.tracking.lineage.operations import (
    add_derivation,
    get_derivation_chain,
    validate_lineage_relationships,
)
from src.core.tracking.operations import add_document


def test_add_document_basic(storage):
    """Test adding a new document without relationships."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)
    lineage = storage.get_lineage(doc_id)
    assert lineage.doc_id == doc_id, "Document ID should be preserved"
    assert not lineage.parents, "New document should have no parents"
    assert not lineage.children, "New document should have no children"


def test_add_document_with_parent(storage):
    """Test adding a document with parent relationship."""
    parent_id = "parent_doc"
    child_id = "child_doc"
    add_document(storage, doc_id=parent_id)
    add_document(storage, doc_id=child_id, parent_ids=[parent_id])

    parent = storage.get_lineage(parent_id)
    child = storage.get_lineage(child_id)

    assert parent_id in child.parents, "Child should reference parent"
    assert child_id in parent.children, "Parent should reference child"


def test_get_derivation_chain(storage):
    """Test getting the derivation chain for a document."""
    doc_ids = ["doc1", "doc2", "doc3", "doc4"]
    add_document(storage, doc_id=doc_ids[0])

    # Create chain of derived documents
    for i in range(1, len(doc_ids)):
        add_document(storage, doc_id=doc_ids[i], parent_ids=[doc_ids[i - 1]])

    # Get chain from last document
    chain = get_derivation_chain(storage, doc_ids[-1])
    assert len(chain) == len(doc_ids), "Chain should include all documents"
    assert [doc.doc_id for doc in chain] == list(
        reversed(doc_ids)
    ), "Chain should be in correct order"


def test_validate_lineage_relationships(storage):
    """Test validation of lineage relationships."""
    # Set up test documents
    doc1_id = "doc1"
    doc2_id = "doc2"
    add_document(storage, doc_id=doc1_id)
    add_document(storage, doc_id=doc2_id, parent_ids=[doc1_id])

    # Validate relationships
    errors = validate_lineage_relationships(storage.get_all_lineage())
    assert len(errors) == 0, "Valid relationships should have no errors"

    # Verify bidirectional references
    doc1 = storage.get_lineage(doc1_id)
    doc2 = storage.get_lineage(doc2_id)
    assert doc2_id in doc1.children, "Parent should reference child"
    assert doc1_id in doc2.parents, "Child should reference parent"


def test_validate_missing_references(storage):
    """Test validation with missing document references."""
    doc_id = "test_doc"
    non_existent = "non_existent_doc"

    # Create document with reference to non-existent parent
    add_document(storage, doc_id=doc_id)
    storage.lineage_data[doc_id].parents.append(non_existent)

    # Validate relationships
    errors = validate_lineage_relationships(storage.get_all_lineage())
    assert any("missing" in error.lower() for error in errors), "Should detect missing references"


def test_circular_reference_prevention(storage):
    """Test prevention of circular references in document lineage."""
    # Create chain: doc1 -> doc2 -> doc3
    doc_ids = ["doc1", "doc2", "doc3"]

    # Create all documents first
    for doc_id in doc_ids:
        add_document(storage, doc_id)

    # Create chain
    add_derivation(storage, parent_id=doc_ids[0], derived_id=doc_ids[1])
    add_derivation(storage, parent_id=doc_ids[1], derived_id=doc_ids[2])

    # Attempt to create circular reference: doc3 -> doc1
    with pytest.raises(ValueError) as exc_info:
        add_derivation(storage, parent_id=doc_ids[2], derived_id=doc_ids[0])
    assert "circular" in str(exc_info.value).lower(), "Should detect circular reference"


def test_multiple_parents(storage):
    """Test document with multiple parent relationships."""
    parent_ids = ["parent1", "parent2", "parent3"]
    child_id = "child"

    # Create parent documents
    for parent_id in parent_ids:
        add_document(storage, doc_id=parent_id)

    # Create child with multiple parents
    add_document(storage, doc_id=child_id, parent_ids=parent_ids)

    # Verify relationships
    child = storage.get_lineage(child_id)
    assert set(child.parents) == set(parent_ids), "Child should reference all parents"

    for parent_id in parent_ids:
        parent = storage.get_lineage(parent_id)
        assert child_id in parent.children, "Each parent should reference child"


def test_add_document_with_metadata(storage):
    """Test adding a document with metadata."""
    doc_id = "test_doc"
    metadata = {"title": "Test Document", "version": "1.0", "author": "Test Author"}

    add_document(storage, doc_id=doc_id, metadata=metadata)
    lineage = storage.get_lineage(doc_id)

    assert lineage.metadata == metadata, "Document metadata should be preserved"


def test_add_document_idempotency(storage):
    """Test that adding the same document twice doesn't modify existing data."""
    doc_id = "test_doc"
    metadata = {"version": "1.0"}

    # Add document first time
    add_document(storage, doc_id=doc_id, metadata=metadata)

    # Attempt to add again with different metadata
    with pytest.raises(ValueError):
        add_document(storage, doc_id=doc_id, metadata={"version": "2.0"})

    # Verify original data is unchanged
    lineage = storage.get_lineage(doc_id)
    assert lineage.metadata == metadata, "Original metadata should be preserved"


def test_add_document_with_nonexistent_parent(storage):
    """Test adding a document with a non-existent parent."""
    doc_id = "test_doc"
    non_existent_parent = "non_existent"

    with pytest.raises(ValueError) as exc:
        add_document(storage, doc_id=doc_id, parent_ids=[non_existent_parent])
    assert "parent" in str(exc.value).lower(), "Should indicate parent does not exist"
