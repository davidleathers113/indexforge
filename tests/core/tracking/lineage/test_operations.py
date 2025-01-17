"""Tests for document lineage operations."""

from datetime import UTC, datetime

import pytest

from src.core.tracking.lineage.operations import (
    add_derivation,
    get_derivation_chain,
    validate_lineage_relationships,
)
from src.core.tracking.models.transformation import TransformationType
from src.core.tracking.operations import add_document


def test_add_derivation_basic(storage, parent_document, child_document):
    """Test adding a basic derivation relationship."""
    add_derivation(
        storage,
        parent_id=parent_document["id"],
        derived_id=child_document["id"],
        transform_type=TransformationType.FORMAT_CONVERSION,
        description="Test derivation",
    )

    parent = storage.get_lineage(parent_document["id"])
    child = storage.get_lineage(child_document["id"])

    assert child_document["id"] in parent.derived_documents
    assert child_document["id"] in parent.children
    assert parent_document["id"] in child.parents
    assert parent_document["id"] == child.derived_from


def test_add_derivation_with_metadata(storage, parent_document, child_document):
    """Test adding a derivation with metadata."""
    metadata = {
        "processor": "test_processor",
        "version": "1.0",
        "timestamp": datetime.now(UTC).isoformat(),
    }
    parameters = {"format": "pdf", "quality": "high"}

    add_derivation(
        storage,
        parent_id=parent_document["id"],
        derived_id=child_document["id"],
        transform_type=TransformationType.FORMAT_CONVERSION,
        description="Test derivation with metadata",
        parameters=parameters,
        metadata=metadata,
    )

    child = storage.get_lineage(child_document["id"])
    assert parent_document["id"] == child.derived_from


def test_add_derivation_invalid_ids(storage):
    """Test adding derivation with invalid document IDs."""
    with pytest.raises(ValueError) as exc:
        add_derivation(storage, parent_id="", derived_id="test")
    assert "must be provided" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        add_derivation(storage, parent_id="test", derived_id="")
    assert "must be provided" in str(exc.value)


def test_add_derivation_self_reference(storage, sample_document):
    """Test prevention of self-referential derivation."""
    doc_id = sample_document["id"]
    with pytest.raises(ValueError) as exc:
        add_derivation(storage, parent_id=doc_id, derived_id=doc_id)
    assert "cannot be derived from itself" in str(exc.value)


def test_add_derivation_nonexistent_documents(storage):
    """Test adding derivation with non-existent documents."""
    with pytest.raises(ValueError) as exc:
        add_derivation(storage, parent_id="nonexistent1", derived_id="nonexistent2")
    assert "Parent document" in str(exc.value)


def test_get_derivation_chain_basic(storage):
    """Test getting a basic derivation chain."""
    # Create chain: doc1 -> doc2 -> doc3
    doc_ids = ["doc1", "doc2", "doc3"]

    # First create all documents
    for doc_id in doc_ids:
        add_document(storage, doc_id)

    # Then add derivation relationships
    for i, doc_id in enumerate(doc_ids[:-1]):
        add_derivation(storage, parent_id=doc_id, derived_id=doc_ids[i + 1])

    # Get chain from last document
    chain = get_derivation_chain(storage, doc_ids[-1])
    assert len(chain) == len(doc_ids)
    assert [doc.doc_id for doc in chain] == list(reversed(doc_ids))


def test_get_derivation_chain_max_depth(storage):
    """Test getting derivation chain with max depth limit."""
    # Create chain: doc1 -> doc2 -> doc3 -> doc4
    doc_ids = ["doc1", "doc2", "doc3", "doc4"]

    # First create all documents
    for doc_id in doc_ids:
        add_document(storage, doc_id)

    # Then add derivation relationships
    for i, doc_id in enumerate(doc_ids[:-1]):
        add_derivation(storage, parent_id=doc_id, derived_id=doc_ids[i + 1])

    # Get chain with depth limit
    max_depth = 2
    chain = get_derivation_chain(storage, doc_ids[-1], max_depth=max_depth)
    assert len(chain) == max_depth
    assert [doc.doc_id for doc in chain] == list(reversed(doc_ids[-max_depth:]))


def test_get_derivation_chain_invalid_depth(storage, sample_document):
    """Test getting derivation chain with invalid max depth."""
    with pytest.raises(ValueError) as exc:
        get_derivation_chain(storage, sample_document["id"], max_depth=0)
    assert "must be None or a positive integer" in str(exc.value)


def test_get_derivation_chain_nonexistent_document(storage):
    """Test getting derivation chain for non-existent document."""
    with pytest.raises(ValueError) as exc:
        get_derivation_chain(storage, "nonexistent")
    assert "not found" in str(exc.value)


def test_validate_lineage_relationships_valid(storage):
    """Test validation of valid lineage relationships."""
    parent_id = "parent"
    child_id = "child"

    # Create both documents first
    add_document(storage, parent_id)
    add_document(storage, child_id)

    # Add derivation relationship
    add_derivation(storage, parent_id=parent_id, derived_id=child_id)

    # Get both lineages and validate
    parent = storage.get_lineage(parent_id)
    child = storage.get_lineage(child_id)
    errors = validate_lineage_relationships([parent, child])
    assert not errors


def test_validate_lineage_relationships_missing_references(storage):
    """Test validation of missing document references."""
    # Create test document
    doc_id = "test_doc"
    add_document(storage, doc_id)

    # Get lineage and add reference to non-existent document
    lineage = storage.get_lineage(doc_id)
    non_existent = "nonexistent_doc"
    lineage.parents.append(non_existent)
    storage.save_lineage(lineage)

    # Validate and check for error
    errors = validate_lineage_relationships([lineage])
    assert len(errors) == 1
    assert "missing parent" in errors[0]


def test_validate_lineage_relationships_inconsistent(storage):
    """Test validation of inconsistent parent-child relationships."""
    # Create parent and child documents
    parent_id = "parent"
    child_id = "child"
    add_document(storage, parent_id)
    add_document(storage, child_id)

    # Get lineages
    parent = storage.get_lineage(parent_id)
    child = storage.get_lineage(child_id)

    # Create inconsistency: add child to parent's children but not parent to child's parents
    parent.children.append(child_id)
    storage.save_lineage(parent)

    # Validate and check for error
    errors = validate_lineage_relationships([parent, child])
    assert len(errors) == 1
    assert "missing parent reference" in errors[0]
