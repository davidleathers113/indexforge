"""Tests for vector index configuration."""
import pytest
from src.indexing.vector_index import VectorIndex

def test_custom_class_name(mock_weaviate_client):
    """Test initialization with custom class name"""
    index = VectorIndex(client_url='http://localhost:8080', class_name='CustomClass', batch_size=100)
    assert index.class_name == 'CustomClass'

def test_custom_batch_size(mock_weaviate_client):
    """Test initialization with custom batch size"""
    index = VectorIndex(client_url='http://localhost:8080', class_name='TestClass', batch_size=50)
    assert index.batch_size == 50

def test_invalid_client_url(mocker):
    """Test error handling for invalid client URL"""
    mocker.patch('weaviate.Client', side_effect=Exception('Connection failed'))
    with pytest.raises(ConnectionError):
        VectorIndex(client_url='invalid://url', class_name='TestClass', batch_size=100)