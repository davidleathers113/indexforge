"""Unit tests for text cleaning operations.

Tests the functionality of text cleaning utilities including whitespace
normalization and character normalization.
"""

import pytest

from src.ml.processing.text.cleaning import clean_text, normalize_whitespace, normalize_characters


def test_clean_text_basic():
    """Test basic text cleaning functionality."""
    text = "  Hello   World\n\n"
    result = clean_text(text)
    assert result == "Hello World"


def test_clean_text_empty():
    """Test cleaning empty text raises error."""
    with pytest.raises(ValueError, match="Input text cannot be None or empty"):
        clean_text("")


def test_normalize_whitespace_basic():
    """Test basic whitespace normalization."""
    text = "Hello  \n  World"
    result = normalize_whitespace(text)
    assert result == "Hello World"


def test_normalize_whitespace_preserve_paragraphs():
    """Test whitespace normalization with paragraph preservation."""
    text = "Hello\n\nWorld\n\n\nTest"
    result = normalize_whitespace(text, preserve_paragraphs=True)
    assert result == "Hello\n\nWorld\n\nTest"


def test_normalize_characters_basic():
    """Test basic character normalization."""
    text = "Hello" World—Test"
    result = normalize_characters(text)
    assert result == '"Hello" World-Test'


def test_normalize_characters_quotes():
    """Test quote normalization."""
    text = ""Hello" 'World'"
    result = normalize_characters(text, replace_quotes=True)
    assert result == '"Hello" \'World\''


def test_normalize_characters_dashes():
    """Test dash normalization."""
    text = "Hello—World–Test"
    result = normalize_characters(text, replace_dashes=True)
    assert result == "Hello-World-Test"


def test_normalize_characters_invalid_form():
    """Test invalid normalization form raises error."""
    with pytest.raises(ValueError, match="Invalid normalization form"):
        normalize_characters("test", form="INVALID")


def test_normalize_characters_no_replacements():
    """Test character normalization without replacements."""
    text = ""Hello—World""
    result = normalize_characters(text, replace_quotes=False, replace_dashes=False)
    assert result == text


def test_clean_text_comprehensive():
    """Test comprehensive text cleaning with all normalizations."""
    text = "  Hello   World\n\n—"Test""
    result = clean_text(text)
    assert result == 'Hello World-"Test"'