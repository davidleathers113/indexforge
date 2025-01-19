"""Tests for vector indexing utilities."""

import numpy as np
import pytest

from src.core.utils.ml.exceptions import DimensionMismatchError, ResourceError, VectorIndexError
from src.core.utils.ml.vectors import VectorIndex


@pytest.fixture
def sample_vectors():
    """Create sample vectors for testing."""
    np.random.seed(42)
    return np.random.rand(100, 10)  # 100 vectors of dimension 10


@pytest.fixture
def vector_index():
    """Create a vector index for testing."""
    return VectorIndex(dimension=10)


def test_initialization():
    """Test successful initialization."""
    index = VectorIndex(dimension=10)
    assert index.dimension == 10
    assert index.get_size() == 0


def test_initialization_invalid_dimension():
    """Test initialization with invalid dimension."""
    with pytest.raises(ValueError, match="Dimension must be positive"):
        VectorIndex(dimension=0)


def test_initialization_invalid_index_type():
    """Test initialization with invalid index type."""
    with pytest.raises(ValueError, match="Unsupported index type"):
        VectorIndex(dimension=10, index_type="INVALID")


def test_add_vectors(vector_index, sample_vectors):
    """Test adding vectors to the index."""
    vector_index.add_vectors(sample_vectors)
    assert vector_index.get_size() == len(sample_vectors)


def test_add_vectors_with_ids(vector_index, sample_vectors):
    """Test adding vectors with explicit IDs."""
    ids = np.arange(len(sample_vectors))
    vector_index.add_vectors(sample_vectors, ids)
    assert vector_index.get_size() == len(sample_vectors)


def test_add_vectors_wrong_dimension(vector_index):
    """Test adding vectors with wrong dimension."""
    wrong_dim_vectors = np.random.rand(10, 5)  # Wrong dimension (5 instead of 10)
    with pytest.raises(ValueError, match="Vectors must have shape"):
        vector_index.add_vectors(wrong_dim_vectors)


def test_add_vectors_wrong_shape(vector_index):
    """Test adding vectors with wrong shape."""
    wrong_shape_vectors = np.random.rand(10)  # 1D array
    with pytest.raises(ValueError, match="Vectors must have shape"):
        vector_index.add_vectors(wrong_shape_vectors)


def test_search(vector_index, sample_vectors):
    """Test vector similarity search."""
    # Add vectors to index
    vector_index.add_vectors(sample_vectors)

    # Search with first vector as query
    query = sample_vectors[:1]
    distances, indices = vector_index.search(query, k=5)

    assert isinstance(distances, np.ndarray)
    assert isinstance(indices, np.ndarray)
    assert distances.shape == (1, 5)
    assert indices.shape == (1, 5)
    assert indices[0, 0] == 0  # First result should be the query vector itself


def test_search_without_distances(vector_index, sample_vectors):
    """Test search without returning distances."""
    vector_index.add_vectors(sample_vectors)
    query = sample_vectors[:1]
    indices = vector_index.search(query, k=5, return_distances=False)

    assert isinstance(indices, np.ndarray)
    assert indices.shape == (1, 5)


def test_search_empty_index(vector_index):
    """Test search on empty index."""
    query = np.random.rand(1, 10)
    with pytest.warns(UserWarning):
        results = vector_index.search(query, k=5)
        assert len(results[1][0]) == 0


def test_search_k_too_large(vector_index, sample_vectors):
    """Test search with k larger than number of vectors."""
    vector_index.add_vectors(sample_vectors[:5])  # Add only 5 vectors
    query = np.random.rand(1, 10)

    with pytest.warns(UserWarning):
        distances, indices = vector_index.search(query, k=10)
        assert distances.shape == (1, 5)  # Should return only 5 results
        assert indices.shape == (1, 5)


def test_reset(vector_index, sample_vectors):
    """Test resetting the index."""
    vector_index.add_vectors(sample_vectors)
    assert vector_index.get_size() > 0

    vector_index.reset()
    assert vector_index.get_size() == 0
