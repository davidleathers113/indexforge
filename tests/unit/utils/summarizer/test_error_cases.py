"""Tests for summarizer error cases."""
import pytest
from src.utils.summarizer import DocumentSummarizer, SummarizerConfig
from tests.fixtures import large_document, mock_cache_manager, sample_document

def test_generate_summary_empty_text(mock_cache_manager):
    """Test summary generation with empty text."""
    summarizer = DocumentSummarizer(model_name='facebook/bart-large-cnn', device=-1, batch_size=4, cache_manager=mock_cache_manager)
    result = summarizer.generate_summary('')
    assert result['status'] == 'error'
    assert result['error'] == 'Empty text'
    assert result['summary'] == ''
    assert result['chunks'] == []

def test_generate_summary(mock_cache_manager, large_document):
    """Test complete summary generation process."""
    summarizer = DocumentSummarizer(model_name='facebook/bart-large-cnn', device=-1, batch_size=4, cache_manager=mock_cache_manager)
    text = large_document['content']['body']
    result = summarizer.generate_summary(text)
    assert result['status'] == 'success'
    assert 'summary' in result
    assert 'chunks' in result
    assert 'metadata' in result
    assert result['metadata']['num_chunks'] > 0

def test_generate_summary_with_config(mock_cache_manager, sample_document):
    """Test summary generation with custom config."""
    summarizer = DocumentSummarizer(model_name='facebook/bart-large-cnn', device=-1, batch_size=4, cache_manager=mock_cache_manager)
    config = SummarizerConfig(max_length=100, min_length=30)
    result = summarizer.generate_summary(sample_document['content']['body'], config)
    assert result['status'] == 'success'
    assert result['metadata']['summary_length'] <= config.max_length