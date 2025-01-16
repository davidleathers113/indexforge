"""Tests for hybrid search operations."""
from unittest.mock import MagicMock

import pytest

from src.indexing.search.search_result import SearchResult
from src.indexing.vector_index import VectorIndex


@pytest.fixture
def search_mock():
    """Create a simple search mock"""
    mock = MagicMock()
    result = SearchResult(id='test-id-0', content={'body': 'Test content'}, metadata={'title': 'Test'}, score=0.85, distance=0.15, vector=[0.1, 0.2, 0.3])
    mock.hybrid_search.return_value = [result]
    return mock


@pytest.fixture
def vector_index(search_mock):
    """Create a VectorIndex instance with mocked search"""
    index = VectorIndex(client_url='http://localhost:8080', class_name='Document', batch_size=100)
    index.operations = MagicMock()
    index.operations.search = search_mock
    return index


def test_hybrid_search(vector_index, search_mock):
    """Test hybrid search functionality"""
    query_vector = [0.1, 0.2, 0.3]
    text_query = 'test query'
    results = vector_index.hybrid_search(text_query, query_vector, limit=5, alpha=0.5)
    assert len(results) == 1
    result = results[0]
    assert result.id == 'test-id-0'
    assert result.score == 0.85
    assert result.distance == 0.15
    search_mock.hybrid_search.assert_called_once_with(text_query, query_vector, 5, 0.5)