"""Text chunking operations.

This module provides functions for splitting text into chunks and
managing chunk overlaps.
"""

import re
from typing import List, Optional

from src.ml.processing.text.cleaning import normalize_whitespace


def chunk_text(
    text: str,
    max_size: int = 1000,
    overlap: int = 100,
    preserve_paragraphs: bool = True,
    min_size: Optional[int] = None,
) -> List[str]:
    """Split text into overlapping chunks.

    Args:
        text: Text to split into chunks
        max_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        preserve_paragraphs: Whether to preserve paragraph breaks
        min_size: Minimum size for the last chunk (if None, uses overlap)

    Returns:
        List of text chunks

    Raises:
        ValueError: If text is empty or parameters are invalid
    """
    if not text:
        raise ValueError("Input text cannot be None or empty")

    if max_size <= 0:
        raise ValueError("max_size must be positive")

    if overlap < 0:
        raise ValueError("overlap must be non-negative")

    if overlap >= max_size:
        raise ValueError("overlap must be less than max_size")

    if min_size is not None and min_size <= 0:
        raise ValueError("min_size must be positive")

    # Normalize whitespace
    text = normalize_whitespace(text, preserve_paragraphs=preserve_paragraphs)

    # Initialize chunks
    chunks = []
    start = 0

    while start < len(text):
        # Find chunk end
        end = find_chunk_boundary(
            text, start=start, max_size=max_size, preserve_paragraphs=preserve_paragraphs
        )

        # Extract chunk
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position
        start = end - overlap if end < len(text) else len(text)

    # Handle minimum size for last chunk
    if min_size is not None and chunks and len(chunks[-1]) < min_size:
        if len(chunks) > 1:
            # Merge last two chunks
            merged = merge_chunks([chunks[-2], chunks[-1]])
            chunks = chunks[:-2] + [merged]

    return chunks


def merge_chunks(chunks: List[str], separator: str = " ") -> str:
    """Merge multiple chunks into a single text.

    Args:
        chunks: List of text chunks to merge
        separator: String to use between chunks

    Returns:
        Merged text

    Raises:
        ValueError: If chunks list is empty
    """
    if not chunks:
        raise ValueError("chunks list cannot be empty")

    return separator.join(chunk.strip() for chunk in chunks)


def find_chunk_boundary(
    text: str, start: int, max_size: int, preserve_paragraphs: bool = True
) -> int:
    """Find appropriate boundary for text chunk.

    Attempts to split at sentence or paragraph boundaries when possible.

    Args:
        text: Full text being chunked
        start: Starting position for this chunk
        max_size: Maximum chunk size
        preserve_paragraphs: Whether to preserve paragraph breaks

    Returns:
        Index for chunk end position
    """
    # Calculate maximum possible end position
    text_len = len(text)
    max_end = min(start + max_size, text_len)

    if max_end == text_len:
        return max_end

    # Try to find paragraph break
    if preserve_paragraphs:
        para_end = text.find("\n\n", start, max_end)
        if para_end != -1:
            return para_end

    # Try to find sentence break
    sent_end = find_sentence_boundary(text, start, max_end)
    if sent_end != -1:
        return sent_end

    # Fall back to word boundary
    word_end = find_word_boundary(text, start, max_end)
    if word_end != -1:
        return word_end

    # If no good boundary found, use max_end
    return max_end


def find_sentence_boundary(text: str, start: int, end: int) -> int:
    """Find sentence boundary in text range.

    Args:
        text: Text to search
        start: Start position
        end: End position

    Returns:
        Position of sentence boundary or -1 if none found
    """
    # Look for sentence-ending punctuation followed by space
    for match in re.finditer(r"[.!?]\s+", text[start:end]):
        return start + match.end()
    return -1


def find_word_boundary(text: str, start: int, end: int) -> int:
    """Find word boundary in text range.

    Args:
        text: Text to search
        start: Start position
        end: End position

    Returns:
        Position of word boundary or -1 if none found
    """
    # Look for whitespace
    for match in re.finditer(r"\s+", text[start:end][::-1]):
        return end - match.start()
    return -1
