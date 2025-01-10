"""Tests for lineage operations functionality."""

from datetime import datetime, timezone

import pytest

from src.connectors.direct_documentation_indexing.source_tracking.document_operations import (
    add_document,
)
from src.connectors.direct_documentation_indexing.source_tracking.enums import ProcessingStatus
from src.connectors.direct_documentation_indexing.source_tracking.lineage_operations import (
    get_derivation_chain,
    validate_lineage_relationships,
)
from src.connectors.direct_documentation_indexing.source_tracking.storage import LineageStorage


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
    """Test prevention of circular references in lineage."""
    doc_ids = ["doc1", "doc2", "doc3"]

    # Create chain of documents
    add_document(storage, doc_id=doc_ids[0])
    add_document(storage, doc_id=doc_ids[1], parent_ids=[doc_ids[0]])
    add_document(storage, doc_id=doc_ids[2], parent_ids=[doc_ids[1]])

    # Attempt to create circular reference
    with pytest.raises(ValueError) as exc_info:
        storage.update_document_lineage(doc_ids[0], {"parents": [doc_ids[2]]})
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


def test_lineage_persistence(temp_lineage_dir):
    """Test persistence of lineage relationships."""
    # Create first storage instance
    storage1 = LineageStorage(str(temp_lineage_dir))
    parent_id = "parent"
    child_id = "child"

    # Add documents with relationship
    add_document(storage1, doc_id=parent_id)
    add_document(storage1, doc_id=child_id, parent_ids=[parent_id])

    # Create new storage instance and verify persistence
    storage2 = LineageStorage(str(temp_lineage_dir))
    parent = storage2.get_lineage(parent_id)
    child = storage2.get_lineage(child_id)

    assert child_id in parent.children, "Parent-child relationship should persist"
    assert parent_id in child.parents, "Child-parent relationship should persist"
