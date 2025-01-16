"""Core utility functions.

This module provides utility functions for text processing, similarity
computation, and validation operations.
"""

from .similarity import (
    compute_cluster_centroids,
    compute_cosine_similarities,
    get_top_similar_indices,
    perform_topic_clustering,
    predict_topic,
)
from .text import (
    calculate_text_similarity,
    chunk_text_by_sentences,
    clean_text,
    find_text_boundaries,
    split_into_sentences,
)
from .validation import (
    detect_circular_references,
    validate_chunk_references,
    validate_document_relationships,
    validate_reference_integrity,
)


__all__ = [
    # Similarity functions
    "compute_cosine_similarities",
    "compute_cluster_centroids",
    "get_top_similar_indices",
    "perform_topic_clustering",
    "predict_topic",
    # Text processing functions
    "clean_text",
    "split_into_sentences",
    "chunk_text_by_sentences",
    "find_text_boundaries",
    "calculate_text_similarity",
    # Validation functions
    "detect_circular_references",
    "validate_chunk_references",
    "validate_document_relationships",
    "validate_reference_integrity",
]
