"""Integration tests for schema management flow."""
import logging
from unittest.mock import patch

import pytest

from src.indexing.vector_index import VectorIndex


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@pytest.fixture
def vector_index(mock_weaviate_client, mock_cache_manager, mock_schema_validator):
    """Create a VectorIndex instance with mocks"""
    with patch('weaviate.Client', return_value=mock_weaviate_client):
        yield VectorIndex(client_url='http://localhost:8080', class_name='Document', batch_size=100, schema_validator=mock_schema_validator)


def test_schema_management_flow(vector_index, mock_weaviate_client, mock_schema_validator):
    """Test complete schema management flow:
    1. Initial schema creation
    2. Schema validation
    3. Schema migration
    4. Schema updates
    """
    logger.info('Step 1: Testing initial schema creation')
    mock_schema_validator.set_schema(None)
    mock_schema_validator.validate_schema.return_value = True
    vector_index.initialize()
    logger.debug('Verifying create_class was called exactly once')
    mock_weaviate_client.schema.create_class.assert_called_once()
    mock_weaviate_client.schema.create_class.reset_mock()
    logger.info('Step 2: Testing existing schema with no changes needed')
    mock_schema_validator.set_schema({'class': 'Document', 'properties': []})
    mock_schema_validator.set_schema_version_valid(True)
    vector_index.initialize()
    logger.debug(f'Verifying create_class call count is still 1, actual: {mock_weaviate_client.schema.create_class.call_count}')
    assert mock_weaviate_client.schema.create_class.call_count == 0
    mock_weaviate_client.schema.create_class.reset_mock()
    mock_weaviate_client.schema.delete_class.reset_mock()
    logger.info('Step 3: Testing schema migration')
    mock_schema_validator.set_schema({'class': 'Document', 'properties': []})
    mock_schema_validator.set_schema_version_valid(False)
    vector_index.initialize()
    logger.debug('Verifying delete_class was called once')
    mock_weaviate_client.schema.delete_class.assert_called_once()
    logger.debug(f'Verifying create_class call count is 1, actual: {mock_weaviate_client.schema.create_class.call_count}')
    assert mock_weaviate_client.schema.create_class.call_count == 1
    mock_weaviate_client.schema.create_class.reset_mock()
    mock_weaviate_client.schema.delete_class.reset_mock()
    logger.info('Step 4: Testing invalid schema handling')
    mock_schema_validator.set_schema({'class': 'Document', 'properties': []})
    mock_schema_validator.set_schema_version_valid(False)
    with patch('src.indexing.schema.schema_definition.SchemaDefinition.get_schema') as mock_get_schema:
        mock_get_schema.return_value = {'class': 'Document', 'vectorizer': 'none', 'properties': []}
        try:
            vector_index.initialize()
            logger.error('Expected ValueError was not raised')
            raise AssertionError('Expected ValueError was not raised')
        except ValueError as e:
            logger.debug(f'Caught expected ValueError: {e!s}')
            assert str(e) == 'Invalid schema configuration'