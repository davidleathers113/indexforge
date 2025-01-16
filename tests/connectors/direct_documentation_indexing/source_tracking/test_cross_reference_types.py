"""Tests for different types of cross-references."""

import numpy as np
import pytest

from src.cross_reference import CrossReferenceManager, ReferenceType


@pytest.fixture
def sample_embeddings():
    """Create sample chunk embeddings for testing."""
    rng = np.random.RandomState(42)
    embeddings = {f"chunk_{i}": rng.rand(10) for i in range(5)}
    # Make chunk_1 and chunk_2 similar
    embeddings["chunk_1"] = embeddings["chunk_2"] * 0.9 + rng.rand(10) * 0.1
    return embeddings


@pytest.fixture
def reference_manager():
    """Create a CrossReferenceManager instance."""
    return CrossReferenceManager(similarity_threshold=0.75, max_semantic_refs=3, n_topics=2)


def test_sequential_references(reference_manager):
    """Test establishing sequential references between chunks."""
    chunk_ids = ["chunk_0", "chunk_1", "chunk_2"]
    for chunk_id in chunk_ids:
        reference_manager.add_chunk(chunk_id, np.random.rand(10))

    reference_manager.establish_sequential_references(chunk_ids)

    # Check middle chunk references
    refs = reference_manager.get_references("chunk_1", ReferenceType.SEQUENTIAL)
    assert len(refs) == 2, "Middle chunk should have two references"
    assert {ref[0] for ref in refs} == {"chunk_0", "chunk_2"}, "Should reference prev and next"

    # Check end chunks
    start_refs = reference_manager.get_references("chunk_0", ReferenceType.SEQUENTIAL)
    end_refs = reference_manager.get_references("chunk_2", ReferenceType.SEQUENTIAL)
    assert len(start_refs) == 1, "Start chunk should have one reference"
    assert len(end_refs) == 1, "End chunk should have one reference"


def test_semantic_references(reference_manager, sample_embeddings):
    """Test establishing semantic references based on similarity."""
    for chunk_id, embedding in sample_embeddings.items():
        reference_manager.add_chunk(chunk_id, embedding)

    reference_manager.establish_semantic_references()

    # Check similar chunks are referenced
    refs = reference_manager.get_references("chunk_1", ReferenceType.SEMANTIC)
    assert any(ref[0] == "chunk_2" for ref in refs), "Similar chunks should be referenced"

    # Check reference is bidirectional
    refs = reference_manager.get_references("chunk_2", ReferenceType.SEMANTIC)
    assert any(ref[0] == "chunk_1" for ref in refs), "Semantic reference should be bidirectional"


def test_topic_references(reference_manager, sample_embeddings):
    """Test establishing topic-based references using clustering."""
    for chunk_id, embedding in sample_embeddings.items():
        reference_manager.add_chunk(chunk_id, embedding)

    reference_manager.establish_topic_references()

    # Verify topic assignments
    assert reference_manager.topic_clusters is not None, "Topics should be assigned"

    # Check topic references
    all_refs = []
    for chunk_id in sample_embeddings:
        refs = reference_manager.get_references(chunk_id, ReferenceType.TOPIC)
        all_refs.extend(refs)

        # Get topic cluster for the chunk
        topic_id = reference_manager.get_topic_cluster(chunk_id)
        assert isinstance(topic_id, int), "Topic ID should be integer"
        assert 0 <= topic_id < reference_manager.n_topics, "Topic ID should be valid"

    assert len(all_refs) > 0, "Should have some topic references"
