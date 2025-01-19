"""Tests for topic clustering utilities."""

import numpy as np
import pytest
from sklearn.cluster import KMeans

from src.core.utils.ml.exceptions import ClusteringError, ConfigurationError, InsufficientDataError
from src.core.utils.ml.topics import ClusteringConfig, TopicClusterer


@pytest.fixture
def sample_embeddings():
    """Create sample embeddings for testing."""
    # Create 20 2D points in 4 distinct clusters
    np.random.seed(42)
    cluster1 = np.random.normal(loc=[-2, -2], scale=0.3, size=(5, 2))
    cluster2 = np.random.normal(loc=[2, 2], scale=0.3, size=(5, 2))
    cluster3 = np.random.normal(loc=[-2, 2], scale=0.3, size=(5, 2))
    cluster4 = np.random.normal(loc=[2, -2], scale=0.3, size=(5, 2))
    return np.vstack([cluster1, cluster2, cluster3, cluster4])


@pytest.fixture
def topic_clusterer():
    """Create a topic clusterer for testing."""
    return TopicClusterer()


def test_initialization():
    """Test successful initialization."""
    clusterer = TopicClusterer()
    assert isinstance(clusterer._models, dict)
    assert len(clusterer._models) == 0


def test_get_optimal_clusters(topic_clusterer, sample_embeddings):
    """Test finding optimal number of clusters."""
    config = ClusteringConfig(min_clusters=2, max_clusters=6)
    n_clusters, score = topic_clusterer._get_optimal_clusters(sample_embeddings, config)

    assert isinstance(n_clusters, int)
    assert 2 <= n_clusters <= 6
    assert isinstance(score, float)
    assert -1 <= score <= 1


def test_get_optimal_clusters_insufficient_data(topic_clusterer):
    """Test handling insufficient data for clustering."""
    embeddings = np.random.rand(1, 10)  # Only one sample
    config = ClusteringConfig(min_clusters=2)

    with pytest.raises(InsufficientDataError):
        topic_clusterer._get_optimal_clusters(embeddings, config)


def test_cluster_documents(topic_clusterer, sample_embeddings):
    """Test document clustering with valid input."""
    result = topic_clusterer.cluster_documents(sample_embeddings)

    assert isinstance(result, dict)
    assert "n_clusters" in result
    assert "labels" in result
    assert "silhouette_score" in result
    assert "cluster_sizes" in result
    assert "cluster_centers" in result

    assert len(result["labels"]) == len(sample_embeddings)
    assert isinstance(result["cluster_sizes"], dict)
    assert isinstance(result["cluster_centers"], list)


def test_cluster_documents_invalid_input(topic_clusterer):
    """Test clustering with invalid input dimensions."""
    invalid_embeddings = np.random.rand(10)  # 1D array

    with pytest.raises(ValueError, match="must be a 2D matrix"):
        topic_clusterer.cluster_documents(invalid_embeddings)


def test_cluster_documents_with_texts(topic_clusterer, sample_embeddings):
    """Test clustering with document texts."""
    texts = [f"Document {i}" for i in range(len(sample_embeddings))]
    result = topic_clusterer.cluster_documents(sample_embeddings, texts=texts)

    assert isinstance(result, dict)
    assert len(result["labels"]) == len(texts)


def test_predict_cluster(topic_clusterer, sample_embeddings):
    """Test cluster prediction for new documents."""
    # First cluster the documents to initialize models
    result = topic_clusterer.cluster_documents(sample_embeddings)
    n_clusters = result["n_clusters"]

    # Test prediction
    new_embedding = np.random.rand(1, sample_embeddings.shape[1])
    cluster_id = topic_clusterer.predict_cluster(new_embedding, n_clusters)

    assert isinstance(cluster_id, int)
    assert 0 <= cluster_id < n_clusters


def test_predict_cluster_invalid_n_clusters(topic_clusterer, sample_embeddings):
    """Test prediction with invalid number of clusters."""
    new_embedding = np.random.rand(1, sample_embeddings.shape[1])

    with pytest.raises(ValueError, match="No model available"):
        topic_clusterer.predict_cluster(new_embedding, n_clusters=999)
