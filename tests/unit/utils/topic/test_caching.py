"""Tests for caching functionality in topic clustering."""
from unittest.mock import Mock, patch
import pytest
from src.utils.topic_clustering import TopicClusterer

@pytest.fixture
def mock_kmeans():
    """Create a mock KMeans clusterer"""
    with patch('src.utils.topic_clustering.KMeans') as mock:
        mock_instance = Mock()
        mock_instance.fit_predict.return_value = [0, 0, 1]
        mock_instance.cluster_centers_ = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
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
    return [{'content': {'body': 'test document 1'}, 'embeddings': {'body': [0.1, 0.2, 0.3]}, 'metadata': {}}, {'content': {'body': 'test document 2'}, 'embeddings': {'body': [0.2, 0.3, 0.4]}, 'metadata': {}}, {'content': {'body': 'test document 3'}, 'embeddings': {'body': [0.7, 0.8, 0.9]}, 'metadata': {}}]

def test_clustering_with_cache(clusterer, mock_cache_manager, sample_documents):
    """Test clustering with cache integration"""
    result1 = clusterer.cluster_documents(sample_documents)
    assert len(result1) == len(sample_documents)
    result2 = clusterer.cluster_documents(sample_documents)
    assert result1 == result2
    mock_cache_manager.get.assert_called()

def test_cache_miss_handling(clusterer, mock_cache_manager, sample_documents):
    """Test handling of cache misses"""
    mock_cache_manager.get.return_value = None
    result = clusterer.cluster_documents(sample_documents)
    assert len(result) == len(sample_documents)
    mock_cache_manager.set.assert_called()

def test_cache_invalidation(clusterer, mock_cache_manager, sample_documents):
    """Test cache invalidation with different documents"""
    result1 = clusterer.cluster_documents(sample_documents)
    modified_docs = sample_documents.copy()
    modified_docs[0]['embeddings']['body'] = [0.9, 0.8, 0.7]
    result2 = clusterer.cluster_documents(modified_docs)
    assert result1 != result2

def test_cache_with_different_configs(clusterer, mock_cache_manager, sample_documents):
    """Test caching with different configurations"""
    from src.utils.topic_clustering import ClusteringConfig
    result1 = clusterer.cluster_documents(sample_documents)
    config = ClusteringConfig(n_clusters=3)
    result2 = clusterer.cluster_documents(sample_documents, config=config)
    assert mock_cache_manager.get.call_count >= 2

def test_cache_error_recovery(clusterer, mock_cache_manager, sample_documents):
    """Test recovery from cache errors"""
    mock_cache_manager.get.side_effect = Exception('Cache error')
    result = clusterer.cluster_documents(sample_documents)
    assert len(result) == len(sample_documents)