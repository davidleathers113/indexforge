"""Tests for text chunking functionality."""
from unittest.mock import Mock, patch

import pytest

from src.utils.text_processing import chunk_text_by_chars, chunk_text_by_words


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


def test_chunk_text_by_chars_no_overlap():
    """Test chunking text by characters without overlap."""
    text = 'abcdefghij' * 3
    chunks = chunk_text_by_chars(text, chunk_size=10)
    assert len(chunks) == 3
    assert all(len(chunk) == 10 for chunk in chunks[:-1])


def test_chunk_text_by_words():
    """Test chunking text by word count."""
    text = 'word ' * 100
    chunks = chunk_text_by_words(text.strip(), max_words=30, overlap_words=5)
    assert len(chunks) > 1
    assert all(len(chunk.split()) <= 30 for chunk in chunks)


def test_chunk_text_by_words_empty():
    """Test chunking empty text by words."""
    chunks = chunk_text_by_words('', max_words=10)
    assert chunks == []


def test_chunk_text_by_words_small_text():
    """Test chunking text smaller than max words."""
    text = 'Small text example'
    chunks = chunk_text_by_words(text, max_words=10)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_overlap_larger_than_size():
    """Test chunking when overlap is larger than chunk size."""
    text = 'test ' * 10
    chunks = chunk_text_by_words(text.strip(), max_words=5, overlap_words=10)
    assert len(chunks) > 0


def test_large_text_handling():
    """Test handling of very large text."""
    large_text = 'word ' * 10000
    char_chunks = chunk_text_by_chars(large_text, chunk_size=1000)
    word_chunks = chunk_text_by_words(large_text, max_words=1000)
    assert all(isinstance(chunk, str) for chunk in char_chunks)
    assert all(isinstance(chunk, str) for chunk in word_chunks)
    assert all(len(chunk) <= 1000 for chunk in char_chunks)
    assert all(len(chunk.split()) <= 1000 for chunk in word_chunks)