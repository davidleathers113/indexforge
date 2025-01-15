"""Tests for schema initialization."""
import pytest

from src.indexing.vector_index import VectorIndex


@pytest.fixture
def index():
    """Create a basic vector index."""
    return VectorIndex(client_url='http://localhost:8080', class_name='Document', batch_size=100)

def test_index_starts_uninitialized(index):
    """Test that a new index starts in uninitialized state."""
    assert not index.is_initialized

def test_index_becomes_initialized(index):
    """Test that initialization marks the index as initialized."""
    index.initialize()
    assert index.is_initialized

def test_initialization_creates_schema(index):
    """Test that initialization creates a schema."""
    assert index.get_schema() is None
    index.initialize()
    assert index.get_schema() is not None