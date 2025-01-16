"""Tests for cross-reference validation and error detection."""

import numpy as np
import pytest

from src.cross_reference import ChunkReference, CrossReferenceManager, ReferenceType


@pytest.fixture
def reference_manager():
    """Create a CrossReferenceManager instance."""
    return CrossReferenceManager(similarity_threshold=0.75, max_semantic_refs=3, n_topics=2)


def test_validate_references_circular(reference_manager):
    """Test detection of circular references."""
    # Create a circular reference chain: chunk_0 -> chunk_1 -> chunk_2 -> chunk_0
    chunks = ["chunk_0", "chunk_1", "chunk_2"]
    for chunk_id in chunks:
        reference_manager.add_chunk(chunk_id, np.random.rand(10))

    reference_manager._add_bidirectional_reference("chunk_0", "chunk_1", ReferenceType.SEQUENTIAL)
    reference_manager._add_bidirectional_reference("chunk_1", "chunk_2", ReferenceType.SEQUENTIAL)
    reference_manager._add_bidirectional_reference("chunk_2", "chunk_0", ReferenceType.SEQUENTIAL)

    errors = reference_manager.validate_references()
    assert any("Circular reference detected" in error for error in errors)


def test_validate_references_orphaned(reference_manager):
    """Test detection of orphaned references."""
    # Create a reference to a non-existent chunk
    reference_manager.add_chunk("chunk_0", np.random.rand(10))
    reference_manager.references["chunk_0"].append(
        ChunkReference(
            source_id="chunk_0", target_id="non_existent", ref_type=ReferenceType.SEQUENTIAL
        )
    )

    errors = reference_manager.validate_references()
    assert any("Orphaned reference" in error for error in errors)


def test_validate_references_missing_backref(reference_manager):
    """Test detection of missing back-references."""
    # Create a one-way reference without the corresponding back-reference
    for chunk_id in ["chunk_0", "chunk_1"]:
        reference_manager.add_chunk(chunk_id, np.random.rand(10))

    reference_manager.references["chunk_0"].append(
        ChunkReference(source_id="chunk_0", target_id="chunk_1", ref_type=ReferenceType.SEQUENTIAL)
    )

    errors = reference_manager.validate_references()
    assert any("Missing back-reference" in error for error in errors)


def test_validate_references_valid(reference_manager):
    """Test validation of valid reference structure."""
    # Create valid bidirectional references
    chunks = ["chunk_0", "chunk_1"]
    for chunk_id in chunks:
        reference_manager.add_chunk(chunk_id, np.random.rand(10))

    reference_manager._add_bidirectional_reference("chunk_0", "chunk_1", ReferenceType.SEQUENTIAL)

    errors = reference_manager.validate_references()
    assert not errors, "Valid reference structure should not produce errors"
