"""Tests for summarizer document processing."""
from unittest.mock import Mock

import pytest

from src.utils.summarizer import DocumentSummarizer


@pytest.fixture
def mock_pipeline():
    """Create a mock pipeline."""
    return Mock(return_value=[{'summary_text': 'Mocked summary'}])


@pytest.fixture
def summarizer(mock_pipeline):
    """Create a document summarizer instance with mocked pipeline."""
    summarizer = DocumentSummarizer()
    summarizer._pipeline = mock_pipeline
    return summarizer


def test_process_documents(summarizer):
    """Test processing multiple documents."""
    documents = [{'content': {'body': 'Document 1'}}, {'content': {'body': 'Document 2'}}]
    processed_docs = summarizer.process_documents(documents)
    assert len(processed_docs) == len(documents)
    for doc in processed_docs:
        assert doc['content']['summary'] is not None
        assert 'summarization' in doc['metadata']
        assert 'compression_ratio' in doc['metadata']['summarization']


def test_process_documents_error_handling(mock_pipeline, summarizer):
    """Test error handling in document processing."""
    mock_pipeline.side_effect = Exception('Model error')
    document = {'content': {'body': 'Test document'}}
    processed_docs = summarizer.process_documents([document])
    assert len(processed_docs) == 1
    assert processed_docs[0]['content']['summary'] is None
    assert 'error' in processed_docs[0]['metadata']['summarization']
    assert 'Model error' in processed_docs[0]['metadata']['summarization']['error']