"""Tests for summarizer chunk processing."""
from unittest.mock import Mock

import pytest

from src.utils.summarizer import DocumentSummarizer, SummarizerConfig
from src.utils.summarizer.pipeline.summarizer import SummarizationError


@pytest.fixture
def mock_pipeline():
    """Create a mock pipeline."""
    return Mock(return_value=[{'summary_text': 'Mocked summary'}])


@pytest.fixture
def summarizer(mock_pipeline):
    """Create a summarizer instance with mocked pipeline."""
    processor = DocumentSummarizer()
    processor._pipeline = mock_pipeline
    return processor


def test_summarize_chunk(mock_pipeline, summarizer):
    """Test summarization of a single text chunk."""
    text = 'This is a test text that needs to be summarized.'
    config = SummarizerConfig()
    result = summarizer.summarizer.summarize_chunk(text)
    assert result == 'Mocked summary'
    mock_pipeline.assert_called_once()
    call_args = mock_pipeline.call_args[1]
    assert call_args['max_length'] == config.max_length
    assert call_args['min_length'] == config.min_length


def test_summarize_chunk_error_handling(mock_pipeline, summarizer):
    """Test error handling in chunk summarization."""
    mock_pipeline.side_effect = Exception('Model error')
    text = 'This is a test text that needs to be summarized.'
    with pytest.raises(SummarizationError) as exc_info:
        summarizer.summarizer.summarize_chunk(text)
    assert 'Failed to summarize chunk' in str(exc_info.value)