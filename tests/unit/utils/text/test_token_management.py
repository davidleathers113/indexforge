"""Tests for text token management functionality."""

from unittest.mock import Mock, patch

import pytest

from src.utils.text_processing import count_tokens, get_token_encoding


@pytest.fixture(scope="function")
def mock_encoding():
    """Create a mock tiktoken encoding."""
    mock = Mock()
    mock.encode.side_effect = lambda text: [0] * (len(text.split()) * 2)
    mock.decode.side_effect = lambda tokens: " ".join(["word"] * (len(tokens) // 2))
    return mock


@pytest.fixture(scope="function")
def mock_tiktoken(mock_encoding):
    """Create a mock tiktoken module."""
    patcher = patch("src.utils.chunking.base.tiktoken")
    mock_tiktoken = patcher.start()
    mock_tiktoken.encoding_for_model.return_value = mock_encoding
    mock_tiktoken.get_encoding.return_value = mock_encoding
    yield mock_tiktoken
    patcher.stop()


def test_get_token_encoding_default(mock_tiktoken, mock_encoding):
    """Test getting default token encoding."""
    encoding = get_token_encoding()
    assert encoding == mock_encoding
    mock_tiktoken.get_encoding.assert_called_once_with("cl100k_base")


def test_get_token_encoding_specific_model(mock_tiktoken, mock_encoding):
    """Test getting token encoding for specific model."""
    encoding = get_token_encoding("gpt-4")
    assert encoding == mock_encoding
    mock_tiktoken.encoding_for_model.assert_called_once_with("gpt-4")


def test_get_token_encoding_invalid_model(mock_tiktoken):
    """Test handling of invalid model name."""
    mock_tiktoken.encoding_for_model.side_effect = KeyError("Invalid model")
    encoding = get_token_encoding("invalid-model")
    assert encoding == mock_tiktoken.get_encoding.return_value


def test_count_tokens(mock_tiktoken, mock_encoding):
    """Test counting tokens in text."""
    text = "This is a test"
    count = count_tokens(text)
    assert count == 8
    mock_encoding.encode.assert_called_once_with(text)


def test_count_tokens_empty_text(mock_tiktoken):
    """Test counting tokens in empty text."""
    assert count_tokens("") == 0
