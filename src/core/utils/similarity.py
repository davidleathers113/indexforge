"""Core similarity utilities.

This module provides utility functions for computing similarities between
vectors and performing clustering operations.
"""

from typing import Dict, List, Tuple

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity


def compute_cosine_similarities(vectors: np.ndarray) -> np.ndarray:
    """Compute pairwise cosine similarities between vectors.

    Args:
        vectors: Array of vectors to compare [n_samples, n_features]

    Returns:
        Array of pairwise similarities [n_samples, n_samples]
    """
    # Normalize vectors
    norms = np.linalg.norm(vectors, axis=1)
    norms[norms == 0] = 1  # Avoid division by zero
    normalized = vectors / norms[:, np.newaxis]

    # Compute similarities
    similarities = cosine_similarity(normalized)

    # Set diagonal to 0 to ignore self-similarity
    np.fill_diagonal(similarities, 0)

    return similarities


def get_top_similar_indices(
    similarities: np.ndarray,
    index: int,
    k: int = 5,
    threshold: float = 0.0,
) -> List[int]:
    """Get indices of top-k most similar vectors.

    Args:
        similarities: Similarity matrix [n_samples, n_samples]
        index: Index of query vector
        k: Number of similar vectors to return
        threshold: Minimum similarity threshold

    Returns:
        List of indices of similar vectors
    """
    # Get similarities for query vector
    scores = similarities[index]

    # Filter by threshold and get top-k
    above_threshold = np.where(scores >= threshold)[0]
    top_k = above_threshold[np.argsort(scores[above_threshold])[-k:]]

    return list(top_k)


def perform_topic_clustering(
    vectors: np.ndarray,
    n_topics: int,
    min_cluster_size: int = 2,
    random_state: int = 42,
) -> Tuple[Dict[int, List[int]], KMeans]:
    """Perform topic clustering on vectors.

    Args:
        vectors: Array of vectors to cluster [n_samples, n_features]
        n_topics: Number of topics (clusters)
        min_cluster_size: Minimum cluster size
        random_state: Random state for reproducibility

    Returns:
        Tuple of (topic_groups, clustering_model) where topic_groups maps
        topic IDs to lists of vector indices
    """
    # Initialize clustering
    kmeans = KMeans(
        n_clusters=n_topics,
        random_state=random_state,
        n_init="auto",
    )

    # Perform clustering
    labels = kmeans.fit_predict(vectors)

    # Group vectors by topic
    topic_groups = {}
    for topic_id in range(n_topics):
        indices = np.where(labels == topic_id)[0]
        if len(indices) >= min_cluster_size:
            topic_groups[topic_id] = list(indices)

    return topic_groups, kmeans


def predict_topic(vector: np.ndarray, clustering_model: KMeans) -> int:
    """Predict topic for a vector.

    Args:
        vector: Vector to predict topic for [n_features]
        clustering_model: Trained clustering model

    Returns:
        Predicted topic ID
    """
    # Reshape vector if needed
    if len(vector.shape) == 1:
        vector = vector.reshape(1, -1)

    return int(clustering_model.predict(vector)[0])


def compute_cluster_centroids(
    vectors: np.ndarray,
    topic_groups: Dict[int, List[int]],
) -> Dict[int, np.ndarray]:
    """Compute centroids for topic clusters.

    Args:
        vectors: Array of vectors [n_samples, n_features]
        topic_groups: Dictionary mapping topic IDs to vector indices

    Returns:
        Dictionary mapping topic IDs to centroid vectors
    """
    centroids = {}
    for topic_id, indices in topic_groups.items():
        if indices:
            centroids[topic_id] = np.mean(vectors[indices], axis=0)
    return centroids
