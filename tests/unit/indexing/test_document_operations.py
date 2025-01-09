"""Tests for vector index document operations."""
import logging
import time
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
import weaviate
from weaviate.exceptions import UnexpectedStatusCodeException
from src.indexing.vector_index import VectorIndex
from tests.fixtures import mock_cache_manager, mock_weaviate_client, sample_document
from tests.fixtures.constants import TEST_UUID
logger = logging.getLogger(__name__)

@pytest.fixture
def mock_delete_404(mock_weaviate_client):
    """Configure mock to raise 404 for nonexistent document"""
    logger.info('Setting up mock_delete_404 fixture')
    mock_weaviate_client.data_object.delete.side_effect = UnexpectedStatusCodeException('Delete object', MagicMock(status_code=404))
    logger.debug('Configured mock to raise 404 error')
    return mock_weaviate_client

@pytest.fixture
def vector_index(mock_delete_404, mock_cache_manager):
    """Create a VectorIndex instance with mocks"""
    logger.info('Setting up vector_index fixture')
    with patch('weaviate.Client', return_value=mock_delete_404):
        index = VectorIndex(client_url='http://localhost:8080', class_name='Document', batch_size=100, test_mode=True)
        logger.debug('Configuring mocks on vector_index')
        index.client = mock_delete_404
        index.cache_manager = mock_cache_manager
        index.operations.client = mock_delete_404
        index.operations.documents.client = mock_delete_404
        index.operations.documents.cache_manager = mock_cache_manager
        index.operations.documents.deduplicate = True
        mock_delete_404.data_object.update.return_value = None
        logger.debug('Vector index setup complete')
        return index

def test_add_documents(vector_index, mock_weaviate_client, sample_document):
    """Test adding documents to the index"""
    doc_ids = vector_index.add_documents([sample_document])
    assert len(doc_ids) == 1
    assert doc_ids[0] == sample_document['uuid']

def test_add_documents_with_deduplication(vector_index, mock_weaviate_client, sample_document):
    """Test document addition with deduplication"""
    docs = [sample_document.copy() for _ in range(3)]
    doc_ids = vector_index.add_documents(docs, deduplicate=True)
    assert len(doc_ids) == 1
    assert doc_ids[0] == sample_document['uuid']

def test_add_documents_batch_processing(vector_index, mock_weaviate_client, sample_document):
    """Test batch processing of documents"""
    docs = []
    for i in range(5):
        doc = sample_document.copy()
        doc['uuid'] = str(uuid.UUID(f'12345678-1234-5678-1234-56781234567{i}'))
        doc['content'] = f'Document {i}'
        docs.append(doc)
    vector_index.batch_size = 2
    doc_ids = vector_index.add_documents(docs, deduplicate=False)
    assert len(doc_ids) == 5
    assert all((doc_ids[i].endswith(f'567{i}') for i in range(5)))

def test_delete_documents(vector_index, mock_delete_404):
    """Test document deletion"""
    logger.info('Starting test_delete_documents')
    logger.debug(f'Attempting to delete document with UUID: {TEST_UUID}')
    logger.debug('Verifying mock configuration')
    assert isinstance(mock_delete_404.data_object.delete.side_effect, UnexpectedStatusCodeException)
    success = vector_index.delete_documents([TEST_UUID])
    logger.debug(f'Delete operation returned: {success}')
    assert success is True
    logger.debug('Success assertion passed')
    logger.debug('Verifying delete method was called')
    mock_delete_404.data_object.delete.assert_called_once_with(TEST_UUID, class_name='Document')
    logger.info('Test completed successfully')

def test_update_document(vector_index, mock_weaviate_client, vector_state):
    """Test document update"""
    vector_state.metadata[TEST_UUID] = {'content': 'test'}
    vector_state.vectors[TEST_UUID] = [0.1] * 1536
    updates = {'content': ['Updated content']}
    success = vector_index.update_document(TEST_UUID, updates)
    assert success is True
    mock_weaviate_client.data_object.update.assert_called_once_with(uuid_str=TEST_UUID, class_name='Document', data_object=updates, vector=None)

def test_update_nonexistent_document(vector_index, mock_weaviate_client):
    """Test updating nonexistent document"""
    mock_weaviate_client.data_object.update.side_effect = Exception('Update of the object not successful! Unexpected status code: 404')
    success = vector_index.update_document('nonexistent', {'content': ['Updated content']})
    assert success is False

def test_delete_error_handling(vector_index, mock_weaviate_client):
    """Test error handling in document deletion"""
    mock_weaviate_client.data_object.delete.side_effect = Exception('Delete object! Unexpected status code: 404')
    success = vector_index.delete_documents(['doc-1'])
    assert success is False

def test_add_documents_with_cache(vector_index, mock_weaviate_client, mock_cache_manager, sample_document):
    """Test document addition with cache"""
    vector_index.add_documents([sample_document], deduplicate=True)
    assert mock_cache_manager.get.call_count > 0
    assert mock_cache_manager.set.call_count > 0