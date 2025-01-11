"""Tests for summarizer cache integration."""
from src.utils.summarizer import DocumentSummarizer, SummarizerConfig

def test_cache_hit(mock_cache_manager, sample_document):
    """Test cache hit when generating summary."""
    summarizer = DocumentSummarizer(model_name='facebook/bart-large-cnn', device=-1, batch_size=4, cache_manager=mock_cache_manager)
    text = sample_document['content']['body']
    result1 = summarizer.generate_summary(text)
    assert result1['status'] == 'success'
    result2 = summarizer.generate_summary(text)
    assert result2['status'] == 'success'
    assert result2['summary'] == result1['summary']
    assert mock_cache_manager.get.called

def test_cache_miss(mock_cache_manager, sample_document):
    """Test cache miss when generating summary."""
    summarizer = DocumentSummarizer(model_name='facebook/bart-large-cnn', device=-1, batch_size=4, cache_manager=mock_cache_manager)
    text = sample_document['content']['body']
    mock_cache_manager.get.return_value = None
    result = summarizer.generate_summary(text)
    assert result['status'] == 'success'
    assert mock_cache_manager.get.called
    assert mock_cache_manager.set.called

def test_cache_with_different_configs(mock_cache_manager, sample_document):
    """Test caching with different configurations."""
    summarizer = DocumentSummarizer(model_name='facebook/bart-large-cnn', device=-1, batch_size=4, cache_manager=mock_cache_manager)
    text = sample_document['content']['body']
    result1 = summarizer.generate_summary(text)
    assert result1['status'] == 'success'
    config = SummarizerConfig(max_length=100, min_length=30)
    result2 = summarizer.generate_summary(text, config)
    assert result2['status'] == 'success'
    assert result1['summary'] != result2['summary']