"""Unit tests for text analysis operations.

Tests the functionality of text analysis utilities including language detection,
encoding detection, and content validation.
"""

import pytest

from src.ml.processing.text.analysis import (
    CHARDET_AVAILABLE,
    LANGDETECT_AVAILABLE,
    check_balanced_delimiters,
    check_format,
    detect_encoding,
    detect_language,
    detect_repetition,
    validate_content,
)


def test_detect_language_basic():
    """Test basic language detection."""
    text = "Hello world, this is a test."
    lang, confidence = detect_language(text)
    assert lang == "en"
    assert confidence > 0.8


def test_detect_language_empty():
    """Test language detection with empty text."""
    with pytest.raises(ValueError, match="Input text cannot be None or empty"):
        detect_language("")


def test_detect_language_low_confidence():
    """Test language detection with low confidence."""
    text = "a b c d"  # Too short/ambiguous
    lang, confidence = detect_language(text, min_confidence=0.9)
    assert lang is None
    assert confidence == 0.0


@pytest.mark.skipif(not LANGDETECT_AVAILABLE, reason="langdetect not installed")
def test_detect_language_multilingual():
    """Test language detection with multilingual text."""
    text = "Hello world. Bonjour le monde."
    lang, confidence = detect_language(text)
    assert lang in ["en", "fr"]  # Could detect either language


def test_detect_encoding_basic():
    """Test basic encoding detection."""
    text = "Hello world".encode("utf-8")
    encoding, confidence = detect_encoding(text)
    assert encoding.lower() == "utf-8"
    assert confidence > 0.8


def test_detect_encoding_empty():
    """Test encoding detection with empty bytes."""
    with pytest.raises(ValueError, match="Input bytes cannot be None or empty"):
        detect_encoding(b"")


@pytest.mark.skipif(not CHARDET_AVAILABLE, reason="chardet not installed")
def test_detect_encoding_various():
    """Test encoding detection with various encodings."""
    encodings = ["utf-8", "ascii", "iso-8859-1"]
    text = "Hello world"

    for enc in encodings:
        encoded = text.encode(enc)
        detected, confidence = detect_encoding(encoded)
        assert detected.lower() in [enc.lower(), "ascii"]  # ASCII is subset of others


def test_validate_content_basic():
    """Test basic content validation."""
    text = "Hello world!"
    errors = validate_content(text)
    assert not errors


def test_validate_content_empty():
    """Test validation of empty content."""
    errors = validate_content("")
    assert len(errors) == 1
    assert "empty" in errors[0].lower()


def test_validate_content_invalid_chars():
    """Test validation with invalid characters."""
    text = "Hello\x00World"
    errors = validate_content(text)
    assert len(errors) == 1
    assert "invalid characters" in errors[0].lower()


def test_validate_content_repetition():
    """Test validation of repetitive content."""
    text = "test test test test test test test test"
    errors = validate_content(text)
    assert len(errors) == 1
    assert "repetition" in errors[0].lower()


def test_validate_content_unbalanced():
    """Test validation of unbalanced delimiters."""
    text = "Hello (world"
    errors = validate_content(text)
    assert len(errors) == 1
    assert "unbalanced" in errors[0].lower()


def test_check_format_sentence():
    """Test sentence format checking."""
    assert check_format("This is a sentence.", "sentence")
    assert not check_format("This is. Two sentences.", "sentence")


def test_check_format_paragraph():
    """Test paragraph format checking."""
    assert check_format("This is a paragraph.", "paragraph")
    assert not check_format("This is.\n\nTwo paragraphs.", "paragraph")


def test_check_format_list():
    """Test list format checking."""
    assert check_format("- Item 1\n- Item 2", "list")
    assert check_format("1. Item 1\n2. Item 2", "list")
    assert not check_format("Regular text", "list")


def test_check_format_code():
    """Test code format checking."""
    assert check_format("def test():\n    pass", "code")
    assert not check_format("Regular text", "code")


def test_check_format_invalid():
    """Test invalid format type."""
    with pytest.raises(ValueError, match="Invalid format type"):
        check_format("test", "invalid_format")


def test_detect_repetition_threshold():
    """Test repetition detection with different thresholds."""
    text = "test test test unique words here"
    assert detect_repetition(text, threshold=0.2)
    assert not detect_repetition(text, threshold=0.8)


def test_check_balanced_delimiters_basic():
    """Test basic delimiter balance checking."""
    assert check_balanced_delimiters("(test)")
    assert check_balanced_delimiters("{[test]}")
    assert not check_balanced_delimiters("(test]")
    assert not check_balanced_delimiters("((test)")
