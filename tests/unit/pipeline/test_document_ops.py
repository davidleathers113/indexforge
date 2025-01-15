import logging
from unittest.mock import Mock

import pytest

from src.pipeline.document_ops import DocumentOperations
from src.utils.document_processing import DocumentMetadata


@pytest.fixture
def mock_components():
    """Create mock components for document operations"""
    return {'summarizer': Mock(), 'embedding_generator': Mock(), 'vector_index': Mock(), 'logger': Mock(spec=logging.Logger)}

@pytest.fixture
def doc_ops(mock_components):
    """Create DocumentOperations instance with mock components"""
    return DocumentOperations(summarizer=mock_components['summarizer'], embedding_generator=mock_components['embedding_generator'], vector_index=mock_components['vector_index'], logger=mock_components['logger'])

def test_document_ops_initialization(doc_ops, mock_components):
    """Test DocumentOperations initialization"""
    assert doc_ops.summarizer == mock_components['summarizer']
    assert doc_ops.embedding_generator == mock_components['embedding_generator']
    assert doc_ops.vector_index == mock_components['vector_index']
    assert doc_ops.logger == mock_components['logger']

def test_update_document_content_only(doc_ops, mock_components):
    """Test updating document content without metadata"""
    doc_id = 'test_doc'
    content = 'Updated content'
    summary = 'Content summary'
    vector = [0.1, 0.2, 0.3]
    mock_components['summarizer'].generate_summary.return_value = {'status': 'success', 'summary': summary}
    mock_components['embedding_generator']._get_embedding.return_value = vector
    mock_components['vector_index'].update_document.return_value = True
    result = doc_ops.update_document(doc_id=doc_id, content=content)
    assert result is True
    mock_components['summarizer'].generate_summary.assert_called_once_with(content)
    mock_components['embedding_generator']._get_embedding.assert_called_once_with(content)
    mock_components['vector_index'].update_document.assert_called_once_with(doc_id=doc_id, updates={'content': {'body': content, 'summary': summary}}, vector=vector)

def test_update_document_metadata_only(doc_ops, mock_components):
    """Test updating document metadata without content"""
    doc_id = 'test_doc'
    metadata = DocumentMetadata(title='Test Document', source='test', timestamp_utc='2024-01-01T00:00:00Z', author='Test Author')
    mock_components['vector_index'].update_document.return_value = True
    result = doc_ops.update_document(doc_id=doc_id, metadata=metadata)
    assert result is True
    mock_components['summarizer'].generate_summary.assert_not_called()
    mock_components['embedding_generator']._get_embedding.assert_not_called()
    mock_components['vector_index'].update_document.assert_called_once_with(doc_id=doc_id, updates={'metadata': metadata.__dict__}, vector=None)

def test_update_document_both_content_and_metadata(doc_ops, mock_components):
    """Test updating both document content and metadata"""
    doc_id = 'test_doc'
    content = 'Updated content'
    metadata = DocumentMetadata(title='Test Document', source='test', timestamp_utc='2024-01-01T00:00:00Z', author='Test Author')
    summary = 'Content summary'
    vector = [0.1, 0.2, 0.3]
    mock_components['summarizer'].generate_summary.return_value = {'status': 'success', 'summary': summary}
    mock_components['embedding_generator']._get_embedding.return_value = vector
    mock_components['vector_index'].update_document.return_value = True
    result = doc_ops.update_document(doc_id=doc_id, content=content, metadata=metadata)
    assert result is True
    mock_components['vector_index'].update_document.assert_called_once_with(doc_id=doc_id, updates={'content': {'body': content, 'summary': summary}, 'metadata': metadata.__dict__}, vector=vector)

def test_update_document_summary_failure(doc_ops, mock_components):
    """Test handling of summary generation failure"""
    doc_id = 'test_doc'
    content = 'Updated content'
    error_msg = 'Summary generation failed'
    mock_components['summarizer'].generate_summary.side_effect = Exception(error_msg)
    mock_components['embedding_generator']._get_embedding.return_value = [0.1, 0.2, 0.3]
    mock_components['vector_index'].update_document.return_value = True
    result = doc_ops.update_document(doc_id=doc_id, content=content)
    assert result is True
    mock_components['vector_index'].update_document.assert_called_once()
    assert 'summary_error' in mock_components['vector_index'].update_document.call_args[1]['updates']['content']
    mock_components['logger'].error.assert_called_with(f'Error generating summary: {error_msg}')

def test_update_document_embedding_failure(doc_ops, mock_components):
    """Test handling of embedding generation failure"""
    doc_id = 'test_doc'
    content = 'Updated content'
    error_msg = 'Embedding generation failed'
    mock_components['summarizer'].generate_summary.return_value = {'status': 'success', 'summary': 'Summary'}
    mock_components['embedding_generator']._get_embedding.side_effect = Exception(error_msg)
    mock_components['vector_index'].update_document.return_value = True
    result = doc_ops.update_document(doc_id=doc_id, content=content)
    assert result is True
    mock_components['vector_index'].update_document.assert_called_once()
    assert mock_components['vector_index'].update_document.call_args[1]['vector'] is None
    mock_components['logger'].error.assert_called_with(f'Error generating embedding: {error_msg}')

def test_update_document_index_failure(doc_ops, mock_components):
    """Test handling of index update failure"""
    doc_id = 'test_doc'
    content = 'Updated content'
    error_msg = 'Index update failed'
    mock_components['vector_index'].update_document.side_effect = Exception(error_msg)
    result = doc_ops.update_document(doc_id=doc_id, content=content)
    assert result is False
    mock_components['logger'].error.assert_called_with(f'Update error: {error_msg}')

def test_delete_documents_success(doc_ops, mock_components):
    """Test successful document deletion"""
    doc_ids = ['doc1', 'doc2', 'doc3']
    mock_components['vector_index'].delete_documents.return_value = True
    result = doc_ops.delete_documents(doc_ids)
    assert result is True
    mock_components['vector_index'].delete_documents.assert_called_once_with(doc_ids=doc_ids)

def test_delete_documents_failure(doc_ops, mock_components):
    """Test handling of document deletion failure"""
    doc_ids = ['doc1', 'doc2']
    error_msg = 'Delete operation failed'
    mock_components['vector_index'].delete_documents.side_effect = Exception(error_msg)
    result = doc_ops.delete_documents(doc_ids)
    assert result is False
    mock_components['logger'].error.assert_called_with(f'Delete error: {error_msg}')

def test_delete_documents_empty_list(doc_ops, mock_components):
    """Test deletion with empty document list"""
    mock_components['vector_index'].delete_documents.return_value = True
    result = doc_ops.delete_documents([])
    assert result is True
    mock_components['vector_index'].delete_documents.assert_called_once_with(doc_ids=[])