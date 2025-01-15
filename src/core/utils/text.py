"""Core text processing utilities.

This module provides utility functions for text processing, including
chunking, cleaning, and normalization operations.
"""

import re
from typing import List, Tuple

import numpy as np


def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and normalizing characters.

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    # Normalize quotes and dashes
    text = text.replace(""", '"').replace(""", '"')
    text = text.replace("'", "'").replace("'", "'")
    text = text.replace("–", "-").replace("—", "-")

    return text


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences.

    Args:
        text: Text to split

    Returns:
        List of sentences
    """
    # Basic sentence splitting on punctuation
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text_by_sentences(
    text: str,
    min_chunk_size: int = 100,
    max_chunk_size: int = 1000,
    overlap: int = 50,
) -> List[Tuple[str, Tuple[int, int]]]:
    """Split text into chunks by sentences.

    Args:
        text: Text to chunk
        min_chunk_size: Minimum chunk size in characters
        max_chunk_size: Maximum chunk size in characters
        overlap: Number of characters to overlap between chunks

    Returns:
        List of (chunk_text, (start_pos, end_pos)) tuples
    """
    chunks = []
    sentences = split_into_sentences(text)
    current_chunk = []
    current_size = 0
    start_pos = 0

    for sentence in sentences:
        sentence_size = len(sentence)

        # If adding this sentence would exceed max_chunk_size,
        # save current chunk and start a new one
        if current_size + sentence_size > max_chunk_size and current_size >= min_chunk_size:
            chunk_text = " ".join(current_chunk)
            end_pos = start_pos + len(chunk_text)
            chunks.append((chunk_text, (start_pos, end_pos)))

            # Start new chunk with overlap
            overlap_text = chunk_text[-overlap:] if overlap > 0 else ""
            start_pos = end_pos - len(overlap_text)
            current_chunk = [overlap_text] if overlap_text else []
            current_size = len(overlap_text)

        current_chunk.append(sentence)
        current_size += sentence_size + 1  # +1 for space

    # Add final chunk if there's anything left
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append((chunk_text, (start_pos, start_pos + len(chunk_text))))

    return chunks


def find_text_boundaries(
    text: str, pattern: str, window_size: int = 100
) -> List[Tuple[int, int, float]]:
    """Find text boundaries around pattern matches.

    Args:
        text: Text to search in
        pattern: Pattern to search for
        window_size: Size of context window around matches

    Returns:
        List of (start_pos, end_pos, score) tuples
    """
    boundaries = []
    matches = list(re.finditer(pattern, text))

    for match in matches:
        start_idx = max(0, match.start() - window_size)
        end_idx = min(len(text), match.end() + window_size)

        # Calculate relevance score based on match position
        center_pos = (match.start() + match.end()) / 2
        distance_to_center = abs(center_pos - (start_idx + end_idx) / 2)
        score = 1.0 - (distance_to_center / window_size)

        boundaries.append((start_idx, end_idx, score))

    return boundaries


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score between 0 and 1
    """
    # Convert texts to character frequency vectors
    chars1 = np.array([text1.count(c) for c in set(text1 + text2)])
    chars2 = np.array([text2.count(c) for c in set(text1 + text2)])

    # Calculate cosine similarity
    dot_product = np.dot(chars1, chars2)
    norm1 = np.linalg.norm(chars1)
    norm2 = np.linalg.norm(chars2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)
