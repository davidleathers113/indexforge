"""Tests for basic cross-reference functionality."""

import numpy as np
import pytest

from src.cross_reference import CrossReferenceManager


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


def test_add_chunk(reference_manager, sample_embeddings):
    """Test adding chunks to the manager."""
    chunk_id = "chunk_0"
    embedding = sample_embeddings[chunk_id]
    reference_manager.add_chunk(chunk_id, embedding)

    assert chunk_id in reference_manager.references, "Chunk should be in references"
    assert chunk_id in reference_manager.embeddings, "Chunk should be in embeddings"
    assert len(reference_manager.references[chunk_id]) == 0, "New chunk should have no references"
    np.testing.assert_array_equal(
        reference_manager.embeddings[chunk_id], embedding, "Embedding should be stored correctly"
    )


def test_add_duplicate_chunk(reference_manager):
    """Test handling of duplicate chunk additions."""
    chunk_id = "test_chunk"
    embedding = np.random.rand(10)

    reference_manager.add_chunk(chunk_id, embedding)
    with pytest.raises(ValueError, match="already exists"):
        reference_manager.add_chunk(chunk_id, embedding)


def test_add_chunk_invalid_embedding(reference_manager):
    """Test handling of invalid embeddings."""
    chunk_id = "test_chunk"
    invalid_embeddings = [
        None,
        np.random.rand(5),  # Wrong dimension
        np.random.rand(10, 2),  # Wrong shape
        [1, 2, 3],  # Wrong type
    ]

    for embedding in invalid_embeddings:
        with pytest.raises((ValueError, TypeError)):
            reference_manager.add_chunk(chunk_id, embedding)
