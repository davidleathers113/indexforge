"""
Utility functions for cross-reference management.

This package provides utility functions for computing similarities between
document chunks and performing topic clustering.
"""

from .clustering import perform_topic_clustering, predict_topic
from .similarity import compute_cosine_similarities, get_top_similar_indices

__all__ = [
    "perform_topic_clustering",
    "predict_topic",
    "compute_cosine_similarities",
    "get_top_similar_indices",
]
