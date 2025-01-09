"""Tests for the document indexer component."""
from typing import List
from unittest.mock import MagicMock, patch
import pytest
from src.pipeline.components.indexer import DocumentIndexer
from src.pipeline.config.settings import PipelineConfig

@pytest.fixture
def config():
    """Create a test configuration."""
    return PipelineConfig(export_dir='test_dir', index_url='http://test:8080', class_name='TestDoc', batch_size=10)

@pytest.fixture
def mock_vector_index():
    """Create a mock vector index."""
    with patch('src.pipeline.components.indexer.VectorIndex') as mock:
        instance = mock.return_value
        instance.add_documents.return_value = ['1', '2']
        yield instance

@pytest.fixture
def indexer(config, mock_vector_index):
    """Create a test indexer."""
    return DocumentIndexer(config=config)

def test_indexer_initialization(config, mock_vector_index):
    """Test indexer initialization."""
    indexer = DocumentIndexer(config=config)
    assert indexer.config == config
    mock_vector_index.assert_called_once_with(client_url=config.index_url, class_name=config.class_name, batch_size=config.batch_size)
    mock_vector_index.return_value.initialize.assert_called_once()

def test_indexer_process_empty(indexer, mock_vector_index):
    """Test processing with no documents."""
    result = indexer.process([])
    assert result == []
    mock_vector_index.add_documents.assert_not_called()

def test_indexer_process_documents(indexer, mock_vector_index):
    """Test processing documents."""
    docs = [{'id': 'old1'}, {'id': 'old2'}]
    mock_vector_index.add_documents.return_value = ['new1', 'new2']
    result = indexer.process(docs)
    assert len(result) == 2
    assert result[0]['id'] == 'new1'
    assert result[1]['id'] == 'new2'
    mock_vector_index.add_documents.assert_called_once_with(docs, deduplicate=False)

def test_indexer_process_with_deduplication(indexer, mock_vector_index):
    """Test processing documents with deduplication."""
    docs = [{'id': '1'}, {'id': '2'}]
    indexer.process(docs, deduplicate=True)
    mock_vector_index.add_documents.assert_called_once_with(docs, deduplicate=True)

def test_indexer_process_error_handling(indexer, mock_vector_index):
    """Test error handling during processing."""
    docs = [{'id': '1'}]
    mock_vector_index.add_documents.side_effect = Exception('Test error')
    result = indexer.process(docs)
    assert result == docs

def test_indexer_cleanup(indexer, mock_vector_index):
    """Test indexer cleanup."""
    indexer.cleanup()
    mock_vector_index.cleanup.assert_called_once()

def test_indexer_cleanup_error_handling(indexer, mock_vector_index):
    """Test error handling during cleanup."""
    mock_vector_index.cleanup.side_effect = Exception('Test error')
    with pytest.raises(Exception):
        indexer.cleanup()