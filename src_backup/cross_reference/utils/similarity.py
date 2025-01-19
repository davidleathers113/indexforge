"""
Similarity computation utilities for cross-reference management.

This module provides functions for computing similarities between document
chunk embeddings, primarily using cosine similarity.
"""


import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def compute_cosine_similarities(embeddings: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between all pairs of embeddings.

    Args:
        embeddings: A 2D numpy array where each row is an embedding vector.

    Returns:
        A 2D numpy array containing pairwise similarity scores.

    Example:
        ```python
        # Compute similarities for 3 embeddings
        embeddings = np.array([
            [1, 0, 1],  # First embedding
            [0, 1, 0],  # Second embedding
            [1, 1, 1]   # Third embedding
        ])
        similarities = compute_cosine_similarities(embeddings)
        print(similarities)  # 3x3 similarity matrix
        ```

    Note:
        The output matrix is symmetric, with diagonal elements = 1.0
        (self-similarity). The similarity scores range from -1 to 1.
    """
    return cosine_similarity(embeddings)


def get_top_similar_indices(
    similarities: np.ndarray, index: int, k: int, threshold: float = 0.0
) -> list[int]:
    """
    Get indices of top-k most similar items for a given item.

    Args:
        similarities: NxN similarity matrix
        index: Index of the item to find similarities for
        k: Number of similar items to return
        threshold: Minimum similarity score threshold

    Returns:
        List of indices of the k most similar items that meet the threshold

    Example:
        ```python
        similarities = compute_cosine_similarities(embeddings)
        # Get top 3 similar items for item 0 with threshold 0.5
        similar_indices = get_top_similar_indices(
            similarities,
            index=0,
            k=3,
            threshold=0.5
        )
        ```
    """
    # Get similarity scores for the specified item
    scores = similarities[index]

    # Sort indices by similarity score (descending)
    sorted_indices = np.argsort(scores)[::-1]

    # Filter out the item itself and scores below threshold
    filtered_indices = [idx for idx in sorted_indices if idx != index and scores[idx] >= threshold]

    # Return top k indices
    return filtered_indices[:k]
