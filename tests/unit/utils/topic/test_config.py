"""Tests for topic clustering configuration."""
import pytest
from src.utils.topic_clustering import ClusteringConfig

def test_clustering_config_defaults():
    """Test ClusteringConfig default values"""
    config = ClusteringConfig()
    assert config.n_clusters == 5
    assert config.min_cluster_size == 3
    assert config.max_clusters == 20
    assert config.random_state == 42

def test_clustering_config_custom_values():
    """Test ClusteringConfig with custom values"""
    config = ClusteringConfig(n_clusters=3, min_cluster_size=2, max_clusters=10, random_state=123)
    assert config.n_clusters == 3
    assert config.min_cluster_size == 2
    assert config.max_clusters == 10
    assert config.random_state == 123