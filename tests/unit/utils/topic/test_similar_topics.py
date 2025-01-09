"""Tests for similar topics functionality."""
from unittest.mock import Mock, patch
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

@pytest.fixture
def sample_documents():
    """Create sample documents for testing"""
    return [{'content': {'body': 'Document one about technology'}, 'embeddings': {'body': [0.1, 0.2, 0.3]}, 'metadata': {'clustering': {'cluster_id': 0, 'keywords': ['technology', 'ai'], 'size': 2}}}, {'content': {'body': 'Document two about technology'}, 'embeddings': {'body': [0.2, 0.3, 0.4]}, 'metadata': {'clustering': {'cluster_id': 0, 'keywords': ['technology', 'ai'], 'size': 2}}}, {'content': {'body': 'Document three about science'}, 'embeddings': {'body': [0.7, 0.8, 0.9]}, 'metadata': {'clustering': {'cluster_id': 1, 'keywords': ['science', 'research'], 'size': 2}}}]

def test_find_similar_topics(clusterer, sample_documents):
    """Test finding similar topics"""
    query_vector = [0.1, 0.2, 0.3]
    results = clusterer.find_similar_topics(query_vector, sample_documents, top_k=2)
    assert isinstance(results, list)
    assert len(results) <= 2
    for result in results:
        assert 'cluster_id' in result
        assert 'similarity' in result
        assert 'size' in result
        assert 'keywords' in result

def test_find_similar_topics_empty(clusterer):
    """Test finding similar topics with empty documents"""
    results = clusterer.find_similar_topics([0.1, 0.2, 0.3], [])
    assert results == []

def test_find_similar_topics_no_clusters(clusterer):
    """Test finding similar topics with unclustered documents"""
    docs = [{'content': {'body': 'test'}, 'metadata': {}}]
    results = clusterer.find_similar_topics([0.1, 0.2, 0.3], docs)
    assert results == []

def test_similar_topics_error_handling(clusterer):
    """Test error handling in similar topics search"""
    results = clusterer.find_similar_topics(None, sample_documents)
    assert results == []
    results = clusterer.find_similar_topics([0.1, 0.2, 0.3], None)
    assert results == []

def test_find_similar_topics_custom_top_k(clusterer, sample_documents):
    """Test finding similar topics with custom top_k"""
    query_vector = [0.1, 0.2, 0.3]
    results = clusterer.find_similar_topics(query_vector, sample_documents, top_k=1)
    assert isinstance(results, list)
    assert len(results) <= 1