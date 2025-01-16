"""Tests for schema validation operations."""
from unittest.mock import patch

import pytest

from src.indexing.vector_index import VectorIndex


@pytest.fixture
def vector_index(mock_weaviate_client, mock_cache_manager):
    """Create a VectorIndex instance with mocks"""
    return VectorIndex(client_url='http://localhost:8080', class_name='Document', batch_size=100)


def test_ensure_schema_existing(vector_index, mock_weaviate_client, mock_schema_validator):
    """Test schema handling when it already exists"""
    mock_schema_validator.get_schema.return_value = {'class': 'Document', 'properties': []}
    mock_schema_validator.check_schema_version.return_value = True
    with patch('src.indexing.schema.schema_migrator.SchemaValidator', return_value=mock_schema_validator):
        vector_index.initialize()
        assert not mock_weaviate_client.schema.create_class.called
        assert not mock_weaviate_client.schema.update_class.called