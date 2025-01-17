"""Integration tests for document operations functionality."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List

import pytest

from src.core.interfaces.storage import LineageStorage
from src.core.tracking.lineage.operations import (
    add_derivation,
    get_derivation_chain,
    validate_lineage_relationships,
)
from src.core.tracking.models.transformation import TransformationType
from src.core.tracking.operations import add_document


@pytest.fixture
def storage_dir(tmp_path) -> Path:
    """Create a temporary storage directory."""
    storage_path = tmp_path / "test_storage"
    storage_path.mkdir()
    return storage_path


@pytest.fixture
def storage(storage_dir) -> LineageStorage:
    """Create a LineageStorage instance."""
    return LineageStorage(str(storage_dir))


@pytest.fixture
def sample_metadata() -> Dict:
    """Create sample document metadata."""
    return {
        "type": "pdf",
        "pages": 10,
        "created_at": datetime.now(UTC).isoformat(),
        "source": "test",
        "version": "1.0",
    }


@pytest.fixture
def document_chain(storage, sample_metadata) -> List[str]:
    """Create a chain of related documents."""
    doc_ids = ["doc1", "doc2", "doc3"]

    # Create initial document
    add_document(storage, doc_id=doc_ids[0], metadata=sample_metadata)

    # Create derived documents
    for i in range(1, len(doc_ids)):
        derived_metadata = sample_metadata.copy()
        derived_metadata.update({"version": f"1.{i}", "derived_from": doc_ids[i - 1]})
        add_document(
            storage, doc_id=doc_ids[i], parent_ids=[doc_ids[i - 1]], metadata=derived_metadata
        )
        add_derivation(
            storage,
            parent_id=doc_ids[i - 1],
            derived_id=doc_ids[i],
            transform_type=TransformationType.UPDATE,
            description=f"Update version 1.{i}",
        )

    return doc_ids


def test_document_creation_persistence(storage: LineageStorage, sample_metadata: Dict):
    """Test that documents are properly created and persisted."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id, metadata=sample_metadata)

    # Create new storage instance to verify persistence
    new_storage = LineageStorage(storage.storage_dir)
    lineage = new_storage.get_lineage(doc_id)

    assert lineage is not None
    assert lineage.doc_id == doc_id
    assert lineage.metadata == sample_metadata


def test_document_relationships_persistence(storage: LineageStorage, document_chain: List[str]):
    """Test that document relationships are properly persisted."""
    # Create new storage instance
    new_storage = LineageStorage(storage.storage_dir)

    # Verify relationships
    for i in range(1, len(document_chain)):
        parent = new_storage.get_lineage(document_chain[i - 1])
        child = new_storage.get_lineage(document_chain[i])

        assert document_chain[i] in parent.children
        assert document_chain[i - 1] in child.parents
        assert document_chain[i] in parent.derived_documents
        assert child.derived_from == document_chain[i - 1]


def test_derivation_chain_consistency(storage: LineageStorage, document_chain: List[str]):
    """Test consistency of derivation chains across storage instances."""
    # Get chain from original storage
    original_chain = get_derivation_chain(storage, document_chain[-1])

    # Create new storage instance and get chain
    new_storage = LineageStorage(storage.storage_dir)
    new_chain = get_derivation_chain(new_storage, document_chain[-1])

    # Compare chains
    assert len(original_chain) == len(new_chain)
    for orig, new in zip(original_chain, new_chain):
        assert orig.doc_id == new.doc_id
        assert orig.metadata == new.metadata
        assert orig.parents == new.parents
        assert orig.children == new.children


def test_concurrent_document_operations(storage: LineageStorage, sample_metadata: Dict):
    """Test handling of concurrent document operations."""
    doc_id = "concurrent_doc"
    parent_id = "parent_doc"

    # Create parent document
    add_document(storage, doc_id=parent_id, metadata=sample_metadata)

    # Create document with relationship
    add_document(storage, doc_id=doc_id, parent_ids=[parent_id], metadata=sample_metadata)

    # Attempt concurrent modification
    with pytest.raises(ValueError):
        add_document(storage, doc_id=doc_id, metadata={"version": "2.0"})

    # Verify original data is preserved
    lineage = storage.get_lineage(doc_id)
    assert lineage.metadata == sample_metadata
    assert parent_id in lineage.parents


def test_cross_instance_validation(storage: LineageStorage, document_chain: List[str]):
    """Test validation of relationships across storage instances."""
    # Create new storage instance
    new_storage = LineageStorage(storage.storage_dir)

    # Get lineages from both instances
    original_lineages = [storage.get_lineage(doc_id) for doc_id in document_chain]
    new_lineages = [new_storage.get_lineage(doc_id) for doc_id in document_chain]

    # Validate relationships in both instances
    original_errors = validate_lineage_relationships(original_lineages)
    new_errors = validate_lineage_relationships(new_lineages)

    assert not original_errors, "Original instance has validation errors"
    assert not new_errors, "New instance has validation errors"


def test_large_document_chain(storage: LineageStorage, sample_metadata: Dict):
    """Test handling of large document chains."""
    chain_length = 50
    doc_ids = [f"doc_{i}" for i in range(chain_length)]

    # Create chain of documents
    for i, doc_id in enumerate(doc_ids):
        metadata = sample_metadata.copy()
        metadata["version"] = f"1.{i}"

        if i == 0:
            add_document(storage, doc_id=doc_id, metadata=metadata)
        else:
            add_document(storage, doc_id=doc_id, parent_ids=[doc_ids[i - 1]], metadata=metadata)
            add_derivation(
                storage,
                parent_id=doc_ids[i - 1],
                derived_id=doc_id,
                transform_type=TransformationType.UPDATE,
            )

    # Verify complete chain
    chain = get_derivation_chain(storage, doc_ids[-1])
    assert len(chain) == chain_length
    assert [doc.doc_id for doc in reversed(chain)] == doc_ids


def test_complex_relationship_graph(storage: LineageStorage, sample_metadata: Dict):
    """Test handling of complex document relationship graphs."""
    # Create documents with multiple relationships
    doc_ids = {
        "root": "root_doc",
        "child1": "child1_doc",
        "child2": "child2_doc",
        "grandchild": "grandchild_doc",
    }

    # Create root document
    add_document(storage, doc_id=doc_ids["root"], metadata=sample_metadata)

    # Create children with single parent
    for child_id in [doc_ids["child1"], doc_ids["child2"]]:
        add_document(
            storage, doc_id=child_id, parent_ids=[doc_ids["root"]], metadata=sample_metadata
        )
        add_derivation(
            storage,
            parent_id=doc_ids["root"],
            derived_id=child_id,
            transform_type=TransformationType.SPLIT,
        )

    # Create grandchild with multiple parents
    add_document(
        storage,
        doc_id=doc_ids["grandchild"],
        parent_ids=[doc_ids["child1"], doc_ids["child2"]],
        metadata=sample_metadata,
    )

    # Add derivation relationships
    for parent_id in [doc_ids["child1"], doc_ids["child2"]]:
        add_derivation(
            storage,
            parent_id=parent_id,
            derived_id=doc_ids["grandchild"],
            transform_type=TransformationType.MERGE,
        )

    # Verify relationships
    grandchild = storage.get_lineage(doc_ids["grandchild"])
    assert len(grandchild.parents) == 2
    assert set(grandchild.parents) == {doc_ids["child1"], doc_ids["child2"]}

    for child_id in [doc_ids["child1"], doc_ids["child2"]]:
        child = storage.get_lineage(child_id)
        assert doc_ids["grandchild"] in child.children
        assert doc_ids["root"] in child.parents
