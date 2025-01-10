"""Tests for document lineage relationship validation."""

import pytest

from src.connectors.direct_documentation_indexing.source_tracking import add_document
from src.connectors.direct_documentation_indexing.source_tracking.lineage_operations import (
    validate_lineage_relationships,
)


def test_self_referential_prevention(storage):
    """Test prevention of self-referential relationships."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)

    with pytest.raises(ValueError) as exc_info:
        storage.update_document_lineage(doc_id, {"parents": [doc_id]})
    assert "self-reference" in str(exc_info.value).lower(), "Should detect self-reference"


def test_bidirectional_references(storage):
    """Test maintenance of bidirectional references."""
    parent_id = "parent"
    child_id = "child"

    # Create parent-child relationship
    add_document(storage, doc_id=parent_id)
    add_document(storage, doc_id=child_id, parent_ids=[parent_id])

    # Verify bidirectional references
    parent = storage.get_lineage(parent_id)
    child = storage.get_lineage(child_id)

    assert child_id in parent.children, "Parent should reference child"
    assert parent_id in child.parents, "Child should reference parent"

    # Update relationship
    storage.update_document_lineage(child_id, {"parents": []})

    # Verify references are removed
    parent = storage.get_lineage(parent_id)
    child = storage.get_lineage(child_id)

    assert child_id not in parent.children, "Parent should not reference removed child"
    assert parent_id not in child.parents, "Child should not reference removed parent"


def test_deep_circular_reference(storage):
    """Test detection of deep circular references."""
    # Create a chain of documents
    doc_ids = ["doc1", "doc2", "doc3", "doc4", "doc5"]
    add_document(storage, doc_id=doc_ids[0])

    for i in range(1, len(doc_ids)):
        add_document(storage, doc_id=doc_ids[i], parent_ids=[doc_ids[i - 1]])

    # Attempt to create circular reference from last to first
    with pytest.raises(ValueError) as exc_info:
        storage.update_document_lineage(doc_ids[0], {"parents": [doc_ids[-1]]})
    assert "circular" in str(exc_info.value).lower(), "Should detect deep circular reference"


def test_orphaned_document_validation(storage):
    """Test validation of orphaned documents."""
    # Create documents without relationships
    doc_ids = ["doc1", "doc2", "doc3"]
    for doc_id in doc_ids:
        add_document(storage, doc_id=doc_id)

    # Validate relationships
    errors = validate_lineage_relationships(storage.get_all_lineage())
    assert len(errors) == 0, "Orphaned documents should be valid"


def test_complex_relationship_graph(storage):
    """Test complex relationship graph with multiple paths."""
    # Create diamond-shaped relationship graph
    #   A
    #  / \
    # B   C
    #  \ /
    #   D

    doc_ids = {"A": "root", "B": "branch1", "C": "branch2", "D": "leaf"}

    # Create root
    add_document(storage, doc_id=doc_ids["A"])

    # Create branches
    add_document(storage, doc_id=doc_ids["B"], parent_ids=[doc_ids["A"]])
    add_document(storage, doc_id=doc_ids["C"], parent_ids=[doc_ids["A"]])

    # Create leaf with multiple parents
    add_document(storage, doc_id=doc_ids["D"], parent_ids=[doc_ids["B"], doc_ids["C"]])

    # Verify relationships
    leaf = storage.get_lineage(doc_ids["D"])
    assert set(leaf.parents) == {doc_ids["B"], doc_ids["C"]}, "Leaf should have both parents"

    for branch in ["B", "C"]:
        branch_doc = storage.get_lineage(doc_ids[branch])
        assert doc_ids["D"] in branch_doc.children, f"Branch {branch} should reference leaf"
        assert doc_ids["A"] in branch_doc.parents, f"Branch {branch} should reference root"


def test_relationship_metadata(storage):
    """Test relationship metadata handling."""
    parent_id = "parent"
    child_id = "child"
    relationship_metadata = {
        "type": "derived",
        "method": "extraction",
        "timestamp": "2023-01-01T00:00:00Z",
    }

    # Create relationship with metadata
    add_document(storage, doc_id=parent_id)
    add_document(
        storage,
        doc_id=child_id,
        parent_ids=[parent_id],
        relationship_metadata=relationship_metadata,
    )

    # Verify metadata persistence
    child = storage.get_lineage(child_id)
    assert (
        child.relationship_metadata.get(parent_id) == relationship_metadata
    ), "Relationship metadata should persist"
