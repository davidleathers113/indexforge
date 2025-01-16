"""Tests for time range search operations."""
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.indexing.search.search_result import SearchResult
from src.indexing.vector_index import VectorIndex


@pytest.fixture
def search_mock():
    """Create a simple search mock"""
    mock = MagicMock()
    mock.time_range_search.return_value = [SearchResult(id='test-id-0', content={'body': 'Test content'}, metadata={'title': 'Test', 'timestamp_utc': '2024-01-01T12:00:00Z'}, score=0.9, distance=0.1, vector=[0.1, 0.2, 0.3])]
    return mock


@pytest.fixture
def vector_index(search_mock):
    """Create a VectorIndex instance with mocked search"""
    index = VectorIndex(client_url='http://localhost:8080', class_name='Document', batch_size=100)
    index.operations = MagicMock()
    index.operations.search = search_mock
    return index


def test_time_range_search(vector_index, search_mock):
    """Test time range search functionality"""
    query_vector = [0.1, 0.2, 0.3]
    start_time = datetime(2024, 1, 1)
    end_time = datetime(2024, 1, 2)
    results = vector_index.time_range_search(start_time, end_time, query_vector, limit=5)
    assert len(results) == 1
    result = results[0]
    assert result.id == 'test-id-0'
    assert result.score == 0.9
    assert result.distance == 0.1
    assert 'timestamp_utc' in result.metadata
    search_mock.time_range_search.assert_called_once_with(start_time, end_time, query_vector, 5)