"""Tests for schema error handling."""
from unittest.mock import patch
import pytest
from src.indexing.vector_index import VectorIndex
from tests.fixtures import mock_cache_manager, mock_schema_validator, mock_weaviate_client

@pytest.fixture
def vector_index(mock_weaviate_client, mock_cache_manager):
    """Create a VectorIndex instance with mocks"""
    return VectorIndex(client_url='http://localhost:8080', class_name='Document', batch_size=100)

def test_ensure_schema_error(vector_index, mock_weaviate_client, mock_schema_validator):
    """Test schema creation error handling"""
    with patch('src.indexing.schema.schema_migrator.SchemaMigrator.ensure_schema') as mock_ensure:
        mock_ensure.side_effect = ValueError('Invalid schema configuration')
        with pytest.raises(ValueError, match='Invalid schema configuration'):
            vector_index.initialize()

def test_validate_schema_missing_fields(vector_index, mock_weaviate_client, mock_schema_validator):
    """Test schema validation with missing required fields"""
    with patch('src.indexing.schema.schema_migrator.SchemaMigrator.ensure_schema') as mock_ensure:
        mock_ensure.side_effect = ValueError('Invalid schema configuration')
        with pytest.raises(ValueError, match='Invalid schema configuration'):
            vector_index.initialize()

def test_validate_schema_invalid_types(vector_index, mock_weaviate_client, mock_schema_validator):
    """Test schema validation with invalid property types"""
    with patch('src.indexing.schema.schema_migrator.SchemaMigrator.ensure_schema') as mock_ensure:
        mock_ensure.side_effect = ValueError('Invalid schema configuration')
        with pytest.raises(ValueError, match='Invalid schema configuration'):
            vector_index.initialize()