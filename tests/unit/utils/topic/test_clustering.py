"""Tests for core topic clustering functionality."""
import pytest

from src.utils.topic_clustering import ClusteringConfig, TopicClusterer


@pytest.fixture
def clusterer(mock_cache_manager, cache_state):
    """Create a TopicClusterer instance with mocks"""
    return TopicClusterer(cache_host='localhost', cache_port=6379)


def test_get_optimal_clusters(clusterer):
    """Test optimal cluster number determination"""
    embeddings = [[0.1, 0.2, 0.3], [0.2, 0.3, 0.4], [0.7, 0.8, 0.9], [0.8, 0.9, 1.0]]
    config = ClusteringConfig(min_cluster_size=2)
    n_clusters = clusterer._get_optimal_clusters(embeddings, config)
    assert isinstance(n_clusters, int)
    assert n_clusters >= 1
    assert n_clusters <= len(embeddings) // config.min_cluster_size


def test_get_optimal_clusters_small_dataset(clusterer):
    """Test optimal clusters with small dataset"""
    embeddings = [[0.1, 0.2, 0.3]]
    config = ClusteringConfig(min_cluster_size=2)
    n_clusters = clusterer._get_optimal_clusters(embeddings, config)
    assert n_clusters == 1


def test_cluster_documents(clusterer, mock_kmeans, kmeans_state, sample_documents, doc_state):
    """Test document clustering functionality"""
    result = clusterer.cluster_documents(sample_documents)
    assert len(result) == len(sample_documents)
    for doc in result:
        assert 'clustering' in doc['metadata']
        cluster_info = doc['metadata']['clustering']
        assert 'cluster_id' in cluster_info
        assert 'cluster_size' in cluster_info
        assert 'keywords' in cluster_info
        assert 'similarity_to_centroid' in cluster_info


def test_cluster_documents_empty(clusterer):
    """Test clustering with empty document list"""
    result = clusterer.cluster_documents([])
    assert result == []


def test_cluster_documents_no_embeddings(clusterer):
    """Test clustering documents without embeddings"""
    docs = [{'content': {'body': 'test'}, 'embeddings': {}, 'metadata': {}}]
    result = clusterer.cluster_documents(docs)
    assert result == docs


def test_cluster_documents_custom_config(clusterer, mock_kmeans, kmeans_state, doc_state, sample_documents):
    """Test clustering with custom configuration"""
    config = ClusteringConfig(n_clusters=3, min_cluster_size=2)
    result = clusterer.cluster_documents(sample_documents, config=config)
    assert len(result) == len(sample_documents)
    mock_kmeans.fit_predict.assert_called_once()


def test_single_cluster_case(clusterer, mock_kmeans, kmeans_state):
    """Test clustering when only one cluster is possible"""
    docs = [{'content': {'body': 'test'}, 'embeddings': {'body': [0.1, 0.2, 0.3]}, 'metadata': {}}]
    result = clusterer.cluster_documents(docs)
    assert len(result) == 1
    assert result[0]['metadata']['clustering']['cluster_id'] == 0


def test_large_document_set(clusterer, mock_kmeans, kmeans_state):
    """Test clustering with a large number of documents"""
    large_docs = []
    for i in range(100):
        large_docs.append({'content': {'body': f'doc {i}'}, 'embeddings': {'body': [0.1, 0.2, 0.3]}, 'metadata': {}})
    result = clusterer.cluster_documents(large_docs)
    assert len(result) == len(large_docs)
    assert all('clustering' in doc['metadata'] for doc in result)