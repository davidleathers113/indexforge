"""Text processing utilities.

This package provides utilities for text processing, including cleaning,
chunking, and similarity computation.
"""

from .chunking import chunk_text_by_sentences, merge_overlapping_chunks
from .processing import clean_text, find_text_boundaries, split_into_sentences
from .similarity import calculate_text_similarity, find_similar_texts

__all__ = [
    # Processing
    "clean_text",
    "split_into_sentences",
    "find_text_boundaries",
    # Chunking
    "chunk_text_by_sentences",
    "merge_overlapping_chunks",
    # Similarity
    "calculate_text_similarity",
    "find_similar_texts",
]
