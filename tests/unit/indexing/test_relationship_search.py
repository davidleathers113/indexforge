"""Tests for relationship search operations."""
from unittest.mock import MagicMock
import pytest
from src.indexing.search.search_result import SearchResult
from src.indexing.vector_index import VectorIndex

@pytest.fixture
def search_mock():
    """Create a simple search mock"""
    mock = MagicMock()
    mock.relationship_search.return_value = [SearchResult(id='test-id-0', content={'body': 'Test content'}, metadata={'title': 'Test', 'parent_id': 'parent-1'}, score=0.9, distance=0.1, vector=[0.1, 0.2, 0.3])]
    return mock

@pytest.fixture
def vector_index(search_mock):
    """Create a VectorIndex instance with mocked search"""
    index = VectorIndex(client_url='http://localhost:8080', class_name='Document', batch_size=100)
    index.operations = MagicMock()
    index.operations.search = search_mock
    return index

def test_relationship_search(vector_index, search_mock):
    """Test relationship search functionality"""
    query_vector = [0.1, 0.2, 0.3]
    parent_id = 'parent-1'
    results = vector_index.relationship_search(parent_id, query_vector, limit=5)
    assert len(results) == 1
    result = results[0]
    assert result.id == 'test-id-0'
    assert result.score == 0.9
    assert result.distance == 0.1
    assert result.metadata['parent_id'] == parent_id
    search_mock.relationship_search.assert_called_once_with(parent_id, query_vector, 5)