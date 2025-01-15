"""Tests for text truncation functionality."""
from unittest.mock import Mock, patch

import pytest

from src.utils.text_processing import truncate_text


@pytest.fixture
def mock_encoding():
    """Create a mock tiktoken encoding."""
    mock = Mock()
    mock.encode.side_effect = lambda text: [0] * (len(text.split()) * 2)
    mock.decode.side_effect = lambda tokens: ' '.join(['word'] * (len(tokens) // 2))
    return mock

@pytest.fixture
def mock_tiktoken(mock_encoding):
    """Create a mock tiktoken module."""
    with patch('src.utils.text_processing.tiktoken') as mock_tiktoken:
        mock_tiktoken.encoding_for_model.return_value = mock_encoding
        mock_tiktoken.get_encoding.return_value = mock_encoding
        yield mock_tiktoken

def test_truncate_text(mock_tiktoken):
    """Test text truncation by token count."""
    text = 'This is a long text that needs truncation'
    truncated = truncate_text(text, max_length=4, use_tokens=True)
    assert len(truncated.split()) == 2
    assert isinstance(truncated, str)

def test_truncate_text_empty(mock_tiktoken):
    """Test truncating empty text."""
    assert truncate_text('', max_length=10, use_tokens=True) == ''

def test_truncate_text_no_truncation_needed(mock_tiktoken):
    """Test truncation when text is already short enough."""
    text = 'Short text'
    result = truncate_text(text, max_length=20, use_tokens=True)
    assert result == text