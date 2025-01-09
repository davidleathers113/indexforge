"""Unit tests for vector index operations."""
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from src.indexing.vector_index import VectorIndex

@pytest.fixture
def vector_index():
    """Create a VectorIndex instance with mocked operations."""
    with patch('src.indexing.index.vector_index.IndexOperations') as mock_ops:
        mock_ops.return_value.class_name = 'Document'
        mock_ops.return_value.documents.batch_size = 100
        index = VectorIndex(client_url='http://localhost:8080', class_name='Document', batch_size=100)
        yield index

def test_initialization():
    """Test VectorIndex initialization."""
    index = VectorIndex(client_url='http://localhost:8080', class_name='TestClass', batch_size=50)
    assert index.class_name == 'TestClass'
    assert index.batch_size == 50

def test_batch_size_property():
    """Test batch size getter and setter."""
    index = VectorIndex(client_url='http://localhost:8080', class_name='TestClass', batch_size=50)
    assert index.batch_size == 50
    index.batch_size = 100
    assert index.batch_size == 100

def test_add_documents(vector_index):
    """Test adding documents."""
    doc = {'uuid': str(uuid.uuid4()), 'content': {'body': 'Test content'}, 'metadata': {'title': 'Test'}, 'embeddings': {'body': [0.1] * 1536}, 'relationships': {'parent_id': None}}
    vector_index.operations.add_documents.return_value = ['test-id']
    doc_ids = vector_index.add_documents([doc])
    assert len(doc_ids) == 1
    vector_index.operations.add_documents.assert_called_once_with([doc])

def test_update_document(vector_index):
    """Test updating a document."""
    updates = {'content': {'body': 'Updated'}}
    vector_index.operations.update_document.return_value = True
    success = vector_index.update_document('test-id', updates)
    assert success is True
    vector_index.operations.update_document.assert_called_once_with('test-id', updates)

def test_delete_documents(vector_index):
    """Test deleting documents."""
    vector_index.operations.delete_documents.return_value = True
    success = vector_index.delete_documents(['test-id'])
    assert success is True
    vector_index.operations.delete_documents.assert_called_once_with(['test-id'])

def test_search_operations(vector_index):
    """Test search operations."""
    mock_results = [{'id': 'test-id', 'score': 0.95}]
    vector_index.operations.search.semantic_search.return_value = mock_results
    results = vector_index.semantic_search(query_vector=[0.1] * 1536)
    assert results == mock_results
    vector_index.operations.search.semantic_search.assert_called_once()

def test_batch_processing_workflow(vector_index):
    """Test batch processing workflow with multiple documents."""
    docs = [{'uuid': str(uuid.uuid4()), 'content': {'body': f'Test content {i}'}, 'metadata': {'title': f'Test {i}'}, 'embeddings': {'body': [0.1] * 1536}, 'relationships': {'parent_id': None}} for i in range(3)]
    vector_index.operations.add_documents.return_value = [f'test-id-{i}' for i in range(3)]
    doc_ids = vector_index.add_documents(docs)
    assert len(doc_ids) == 3
    vector_index.operations.add_documents.assert_called_once_with(docs)
    updates = {'metadata': {'processed': True}}
    vector_index.operations.update_document.return_value = True
    for doc_id in doc_ids:
        success = vector_index.update_document(doc_id, updates)
        assert success is True
        vector_index.operations.update_document.assert_any_call(doc_id, updates)
    vector_index.operations.delete_documents.return_value = True
    success = vector_index.delete_documents(doc_ids)
    assert success is True
    vector_index.operations.delete_documents.assert_called_once_with(doc_ids)