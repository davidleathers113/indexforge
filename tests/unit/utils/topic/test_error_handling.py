"""Tests for error handling in topic clustering."""
from unittest.mock import Mock, patch

import pytest

from src.utils.topic_clustering import TopicClusterer


@pytest.fixture
def mock_kmeans():
    """Create a mock KMeans clusterer"""
    with patch('src.utils.topic_clustering.KMeans') as mock:
        mock_instance = Mock()
        mock_instance.fit_predict.side_effect = Exception('Clustering error')
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager"""
    with patch('src.utils.topic_clustering.CacheManager') as mock:
        yield mock.return_value


@pytest.fixture
def clusterer(mock_cache_manager):
    """Create a TopicClusterer instance with mocks"""
    return TopicClusterer(cache_host='localhost', cache_port=6379)


@pytest.fixture
def sample_documents():
    """Create sample documents for testing"""
    return [{'content': {'body': 'test document'}, 'embeddings': {'body': [0.1, 0.2, 0.3]}, 'metadata': {}}]


def test_clustering_error_handling(clusterer, mock_kmeans):
    """Test error handling in clustering"""
    result = clusterer.cluster_documents(sample_documents)
    assert result == sample_documents


def test_clustering_invalid_input(clusterer):
    """Test clustering with invalid input"""
    result = clusterer.cluster_documents(None)
    assert result == []
    invalid_docs = [{'invalid': 'format'}]
    result = clusterer.cluster_documents(invalid_docs)
    assert result == invalid_docs


def test_clustering_empty_embeddings(clusterer):
    """Test clustering with empty embeddings"""
    docs = [{'content': {'body': 'test'}, 'embeddings': {}, 'metadata': {}}]
    result = clusterer.cluster_documents(docs)
    assert result == docs


def test_clustering_missing_content(clusterer):
    """Test clustering with missing content"""
    docs = [{'embeddings': {'body': [0.1, 0.2, 0.3]}, 'metadata': {}}]
    result = clusterer.cluster_documents(docs)
    assert result == docs


def test_clustering_with_cache_error(clusterer, mock_cache_manager):
    """Test clustering when cache operations fail"""
    mock_cache_manager.get.side_effect = Exception('Cache error')
    mock_cache_manager.set.side_effect = Exception('Cache error')
    result = clusterer.cluster_documents(sample_documents)
    assert len(result) == len(sample_documents)