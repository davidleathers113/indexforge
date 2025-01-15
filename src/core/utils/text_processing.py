"""Text processing utilities.

This module provides functions for text manipulation, cleaning,
chunking, and similarity computation.
"""

import re
from typing import List, Tuple

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and normalizing characters.

    Args:
        text: The text to clean.

    Returns:
        The cleaned text.
    """
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    # Normalize quotes and dashes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(""", "'").replace(""", "'")
    text = text.replace("–", "-").replace("—", "-")

    return text


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences based on punctuation.

    Args:
        text: The text to split.

    Returns:
        A list of sentences.
    """
    # Split on sentence-ending punctuation followed by whitespace
    sentences = re.split(r"(?<=[.!?])\s+", text)

    # Filter out empty sentences and strip whitespace
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


def chunk_text_by_sentences(
    text: str, min_chunk_size: int = 100, max_chunk_size: int = 1000, overlap: int = 50
) -> List[Tuple[str, int, int]]:
    """Split text into chunks by sentences with specified size constraints.

    Args:
        text: The text to chunk.
        min_chunk_size: Minimum chunk size in characters.
        max_chunk_size: Maximum chunk size in characters.
        overlap: Number of characters to overlap between chunks.

    Returns:
        A list of tuples containing (chunk_text, start_offset, end_offset).
    """
    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_size = 0
    start_offset = 0

    for sentence in sentences:
        sentence_size = len(sentence)

        if current_size + sentence_size > max_chunk_size and current_chunk:
            # Store current chunk
            chunk_text = " ".join(current_chunk)
            end_offset = start_offset + len(chunk_text)
            chunks.append((chunk_text, start_offset, end_offset))

            # Start new chunk with overlap
            overlap_text = chunk_text[-overlap:] if overlap > 0 else ""
            start_offset = end_offset - len(overlap_text)
            current_chunk = [sentence]
            current_size = sentence_size
        else:
            current_chunk.append(sentence)
            current_size += sentence_size

    # Add final chunk if it meets minimum size
    if current_chunk and current_size >= min_chunk_size:
        chunk_text = " ".join(current_chunk)
        end_offset = start_offset + len(chunk_text)
        chunks.append((chunk_text, start_offset, end_offset))

    return chunks


def find_text_boundaries(
    text: str, pattern: str, window_size: int = 100
) -> List[Tuple[str, int, int]]:
    """Find text boundaries around pattern matches with context window.

    Args:
        text: The text to search.
        pattern: The pattern to match.
        window_size: Size of context window around matches.

    Returns:
        A list of tuples containing (context_text, start_offset, end_offset).
    """
    matches = []
    for match in re.finditer(pattern, text):
        start = max(0, match.start() - window_size)
        end = min(len(text), match.end() + window_size)
        context = text[start:end]
        matches.append((context, start, end))
    return matches


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate cosine similarity between two texts using TF-IDF vectors.

    Args:
        text1: First text.
        text2: Second text.

    Returns:
        Similarity score between 0 and 1.
    """
    if not SKLEARN_AVAILABLE:
        return 0.0

    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(similarity)
    except ValueError:
        return 0.0
