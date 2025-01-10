"""Tests for document relationship management."""

import pytest

from src.connectors.direct_documentation_indexing.source_tracking import add_document


def test_add_document_with_parent(storage):
    """Test adding a document with a single parent."""
    parent_id = "parent_doc"
    child_id = "child_doc"

    add_document(storage, doc_id=parent_id)
    add_document(storage, doc_id=child_id, parent_ids=[parent_id])

    parent = storage.get_lineage(parent_id)
    child = storage.get_lineage(child_id)

    assert child_id in parent.children, "Parent should reference child"
    assert parent_id in child.parents, "Child should reference parent"
    assert child.derived_from == parent_id, "First parent should be derivation source"


def test_add_document_with_multiple_parents(storage):
    """Test adding a document with multiple parents."""
    parent_ids = ["parent1", "parent2"]
    child_id = "child_doc"

    for parent_id in parent_ids:
        add_document(storage, doc_id=parent_id)
    add_document(storage, doc_id=child_id, parent_ids=parent_ids)

    child = storage.get_lineage(child_id)
    assert set(child.parents) == set(parent_ids), "Child should reference all parents"
    assert child.derived_from == parent_ids[0], "First parent should be derivation source"

    for parent_id in parent_ids:
        parent = storage.get_lineage(parent_id)
        assert child_id in parent.children, f"Parent {parent_id} should reference child"


def test_add_document_nonexistent_parent(storage):
    """Test handling of nonexistent parent references."""
    with pytest.raises(ValueError, match="Parent document .* not found"):
        add_document(storage, doc_id="child", parent_ids=["nonexistent"])


def test_add_document_circular_reference(storage):
    """Test prevention of circular parent-child relationships."""
    # Create initial parent-child relationship
    add_document(storage, doc_id="parent")
    add_document(storage, doc_id="child", parent_ids=["parent"])

    # Attempt to create circular reference
    with pytest.raises(ValueError, match="Circular reference detected"):
        add_document(storage, doc_id="grandchild", parent_ids=["child"])
        add_document(storage, doc_id="parent", parent_ids=["grandchild"])


def test_add_document_self_reference(storage):
    """Test prevention of self-referential relationships."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)

    with pytest.raises(ValueError, match="Circular reference detected"):
        add_document(storage, doc_id="new_doc", parent_ids=[doc_id, "new_doc"])
