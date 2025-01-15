"""Tests for topic keyword extraction functionality."""
from unittest.mock import patch

import pytest

from src.utils.topic_clustering import TopicClusterer


@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager"""
    with patch('src.utils.topic_clustering.CacheManager') as mock:
        yield mock.return_value

@pytest.fixture
def clusterer(mock_cache_manager):
    """Create a TopicClusterer instance with mocks"""
    return TopicClusterer(cache_host='localhost', cache_port=6379)

def test_get_cluster_keywords(clusterer):
    """Test cluster keyword extraction"""
    embeddings = [[0.1, 0.2, 0.3], [0.2, 0.3, 0.4]]
    texts = ['technology artificial intelligence', 'machine learning data science']
    centroid = [0.15, 0.25, 0.35]
    keywords = clusterer._get_cluster_keywords(embeddings, texts, centroid, top_k=3)
    assert isinstance(keywords, list)
    assert len(keywords) <= 3
    assert all((isinstance(k, str) for k in keywords))

def test_get_cluster_keywords_empty(clusterer):
    """Test keyword extraction with empty inputs"""
    keywords = clusterer._get_cluster_keywords([], [], [0.1, 0.2, 0.3])
    assert keywords == []

def test_get_cluster_keywords_single_doc(clusterer):
    """Test keyword extraction with single document"""
    embeddings = [[0.1, 0.2, 0.3]]
    texts = ['artificial intelligence']
    centroid = [0.1, 0.2, 0.3]
    keywords = clusterer._get_cluster_keywords(embeddings, texts, centroid)
    assert isinstance(keywords, list)
    assert all((isinstance(k, str) for k in keywords))

def test_get_cluster_keywords_custom_top_k(clusterer):
    """Test keyword extraction with custom top_k"""
    embeddings = [[0.1, 0.2, 0.3], [0.2, 0.3, 0.4], [0.3, 0.4, 0.5]]
    texts = ['artificial intelligence machine', 'learning data science', 'neural networks deep']
    centroid = [0.2, 0.3, 0.4]
    keywords = clusterer._get_cluster_keywords(embeddings, texts, centroid, top_k=5)
    assert isinstance(keywords, list)
    assert len(keywords) <= 5
    assert all((isinstance(k, str) for k in keywords))