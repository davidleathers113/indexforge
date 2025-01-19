"""Text chunking utilities.

This module provides functions for splitting text into chunks while preserving
semantic boundaries and managing overlapping segments.
"""

from typing import List, Tuple

from .processing import split_into_sentences


def chunk_text_by_sentences(
    text: str, min_chunk_size: int = 100, max_chunk_size: int = 1000, overlap: int = 50
) -> List[Tuple[str, Tuple[int, int]]]:
    """Split text into overlapping chunks based on sentence boundaries.

    Args:
        text: Text to split into chunks
        min_chunk_size: Minimum chunk size in characters
        max_chunk_size: Maximum chunk size in characters
        overlap: Number of characters to overlap between chunks

    Returns:
        List of tuples containing (chunk_text, (start_pos, end_pos))

    Raises:
        ValueError: If chunking parameters are invalid
    """
    if not text:
        raise ValueError("Input text cannot be empty")
    if min_chunk_size <= 0 or max_chunk_size <= 0:
        raise ValueError("Chunk sizes must be positive")
    if min_chunk_size > max_chunk_size:
        raise ValueError("min_chunk_size cannot be greater than max_chunk_size")
    if overlap < 0:
        raise ValueError("Overlap must be non-negative")
    if overlap >= min_chunk_size:
        raise ValueError("Overlap must be less than min_chunk_size")

    sentences = split_into_sentences(text)
    if not sentences:
        return []

    chunks = []
    current_chunk = []
    current_size = 0
    chunk_start = 0

    for sentence in sentences:
        sentence_size = len(sentence)

        # If single sentence exceeds max size, split it
        if sentence_size > max_chunk_size:
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunk_end = text.find(chunk_text) + len(chunk_text)
                chunks.append((chunk_text, (chunk_start, chunk_end)))
                current_chunk = []
                current_size = 0

            # Split long sentence
            words = sentence.split()
            temp_chunk = []
            temp_size = 0

            for word in words:
                word_size = len(word) + 1  # +1 for space
                if temp_size + word_size > max_chunk_size and temp_chunk:
                    chunk_text = " ".join(temp_chunk)
                    chunk_end = text.find(chunk_text) + len(chunk_text)
                    chunks.append((chunk_text, (chunk_start, chunk_end)))
                    chunk_start = chunk_end - overlap
                    temp_chunk = []
                    temp_size = 0
                temp_chunk.append(word)
                temp_size += word_size

            if temp_chunk:
                chunk_text = " ".join(temp_chunk)
                chunk_end = text.find(chunk_text) + len(chunk_text)
                chunks.append((chunk_text, (chunk_start, chunk_end)))
                chunk_start = chunk_end - overlap
            continue

        # Check if adding sentence exceeds max size
        if current_size + sentence_size > max_chunk_size and current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_end = text.find(chunk_text) + len(chunk_text)
            chunks.append((chunk_text, (chunk_start, chunk_end)))

            # Start new chunk with overlap
            overlap_start = max(0, len(chunk_text) - overlap)
            current_chunk = [chunk_text[overlap_start:]]
            current_size = len(current_chunk[0])
            chunk_start = chunk_end - overlap

        current_chunk.append(sentence)
        current_size += sentence_size

        # Check if current chunk exceeds min size
        if current_size >= min_chunk_size:
            chunk_text = " ".join(current_chunk)
            chunk_end = text.find(chunk_text) + len(chunk_text)
            chunks.append((chunk_text, (chunk_start, chunk_end)))
            chunk_start = chunk_end - overlap
            current_chunk = []
            current_size = 0

    # Add remaining text as final chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunk_end = text.find(chunk_text) + len(chunk_text)
        chunks.append((chunk_text, (chunk_start, chunk_end)))

    return chunks


def merge_overlapping_chunks(
    chunks: List[Tuple[str, Tuple[int, int]]], min_overlap: int = 20
) -> List[Tuple[str, Tuple[int, int]]]:
    """Merge chunks with significant overlap.

    Args:
        chunks: List of text chunks with positions
        min_overlap: Minimum characters overlap to merge chunks

    Returns:
        List of merged chunks with positions

    Raises:
        ValueError: If input chunks are invalid
    """
    if not chunks:
        return []
    if min_overlap < 0:
        raise ValueError("min_overlap must be non-negative")

    merged = []
    current_chunk = chunks[0]

    for next_chunk in chunks[1:]:
        curr_text, (curr_start, curr_end) = current_chunk
        next_text, (next_start, next_end) = next_chunk

        # Check for significant overlap
        overlap = curr_end - next_start
        if overlap >= min_overlap:
            # Merge chunks
            merged_text = curr_text + next_text[overlap:]
            current_chunk = (merged_text, (curr_start, next_end))
        else:
            merged.append(current_chunk)
            current_chunk = next_chunk

    merged.append(current_chunk)
    return merged
