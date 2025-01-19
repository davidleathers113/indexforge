"""Unit tests for text chunking operations.

Tests the functionality of text chunking utilities including chunk splitting,
boundary detection, and chunk merging.
"""

import pytest

from src.ml.processing.text.chunking import (
    chunk_text,
    find_chunk_boundary,
    find_sentence_boundary,
    find_word_boundary,
    merge_chunks,
)


def test_chunk_text_basic():
    """Test basic text chunking functionality."""
    text = "This is a test. Another sentence. And one more."
    chunks = chunk_text(text, max_size=20, overlap=5)
    assert len(chunks) > 1
    assert all(len(chunk) <= 20 for chunk in chunks)


def test_chunk_text_empty():
    """Test chunking empty text raises error."""
    with pytest.raises(ValueError, match="Input text cannot be None or empty"):
        chunk_text("")


def test_chunk_text_invalid_size():
    """Test chunking with invalid size parameters."""
    text = "Test text"
    with pytest.raises(ValueError, match="max_size must be positive"):
        chunk_text(text, max_size=0)

    with pytest.raises(ValueError, match="overlap must be non-negative"):
        chunk_text(text, max_size=10, overlap=-1)

    with pytest.raises(ValueError, match="overlap must be less than max_size"):
        chunk_text(text, max_size=10, overlap=10)


def test_chunk_text_preserve_paragraphs():
    """Test chunking with paragraph preservation."""
    text = "First paragraph.\n\nSecond one.\n\nThird paragraph."
    chunks = chunk_text(text, max_size=50, preserve_paragraphs=True)
    assert any("\n\n" in chunk for chunk in chunks)


def test_chunk_text_min_size():
    """Test chunking with minimum size constraint."""
    text = "Short text. Another bit. More text here."
    chunks = chunk_text(text, max_size=20, min_size=15)
    assert all(len(chunk) >= 15 for chunk in chunks)


def test_merge_chunks_basic():
    """Test basic chunk merging."""
    chunks = ["Hello", "world", "test"]
    result = merge_chunks(chunks)
    assert result == "Hello world test"


def test_merge_chunks_empty():
    """Test merging empty chunks list raises error."""
    with pytest.raises(ValueError, match="chunks list cannot be empty"):
        merge_chunks([])


def test_merge_chunks_custom_separator():
    """Test merging with custom separator."""
    chunks = ["Hello", "world"]
    result = merge_chunks(chunks, separator="-")
    assert result == "Hello-world"


def test_find_chunk_boundary_basic():
    """Test basic boundary detection."""
    text = "First sentence. Second one."
    boundary = find_chunk_boundary(text, start=0, max_size=20)
    assert 0 < boundary <= 20


def test_find_chunk_boundary_paragraph():
    """Test boundary detection with paragraphs."""
    text = "First para.\n\nSecond para."
    boundary = find_chunk_boundary(text, start=0, max_size=20, preserve_paragraphs=True)
    assert text[boundary - 2 : boundary] == "\n\n"


def test_find_sentence_boundary_basic():
    """Test basic sentence boundary detection."""
    text = "First sentence. Second one"
    boundary = find_sentence_boundary(text, 0, len(text))
    assert text[boundary - 2 : boundary] == ". "


def test_find_sentence_boundary_not_found():
    """Test sentence boundary detection with no boundary."""
    text = "No sentence boundary here"
    boundary = find_sentence_boundary(text, 0, len(text))
    assert boundary == -1


def test_find_word_boundary_basic():
    """Test basic word boundary detection."""
    text = "First second"
    boundary = find_word_boundary(text, 0, len(text))
    assert text[boundary - 1] == " "


def test_find_word_boundary_not_found():
    """Test word boundary detection with no boundary."""
    text = "NoSpaces"
    boundary = find_word_boundary(text, 0, len(text))
    assert boundary == -1


def test_chunk_text_comprehensive():
    """Test comprehensive chunking with all features."""
    text = "First paragraph.\n\nSecond paragraph with multiple sentences. More text here.\n\nThird."
    chunks = chunk_text(text, max_size=30, overlap=10, preserve_paragraphs=True, min_size=20)

    # Verify chunk properties
    assert len(chunks) > 1
    assert all(len(chunk) <= 30 for chunk in chunks)
    assert all(len(chunk) >= 20 for chunk in chunks[:-1])  # Except last chunk

    # Verify content preservation
    merged = merge_chunks(chunks)
    assert "First paragraph" in merged
    assert "Second paragraph" in merged
    assert "Third" in merged
