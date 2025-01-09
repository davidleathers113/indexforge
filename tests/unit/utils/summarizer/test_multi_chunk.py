"""Tests for summarizer multi-chunk processing."""
import pytest
from src.utils.summarizer import DocumentSummarizer, SummarizerConfig
from tests.fixtures import mock_cache_manager

def test_combine_summaries(mock_cache_manager):
    """Test combining multiple chunk summaries."""
    summarizer = DocumentSummarizer(model_name='facebook/bart-large-cnn', device=-1, batch_size=4, cache_manager=mock_cache_manager)
    summaries = ['Summary of first chunk.', 'Summary of second chunk.', 'Summary of third chunk.']
    combined = summarizer._combine_summaries(summaries, SummarizerConfig())
    assert isinstance(combined, str)
    assert combined

def test_combine_summaries_single_chunk(mock_cache_manager):
    """Test combining single summary."""
    summarizer = DocumentSummarizer(model_name='facebook/bart-large-cnn', device=-1, batch_size=4, cache_manager=mock_cache_manager)
    summaries = ['Single summary']
    result = summarizer._combine_summaries(summaries, SummarizerConfig())
    assert result == 'Single summary'

def test_combine_summaries_empty(mock_cache_manager):
    """Test combining empty summaries list."""
    summarizer = DocumentSummarizer(model_name='facebook/bart-large-cnn', device=-1, batch_size=4, cache_manager=mock_cache_manager)
    result = summarizer._combine_summaries([], SummarizerConfig())
    assert result == ''