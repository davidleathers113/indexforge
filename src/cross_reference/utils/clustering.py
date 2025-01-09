"""
Topic clustering utilities for cross-reference management.

This module provides functions for clustering document chunks into topics
using k-means clustering on their embeddings.
"""

from typing import Dict, List, Tuple

import numpy as np
from sklearn.cluster import KMeans


def perform_topic_clustering(
    embeddings: np.ndarray, n_topics: int, random_state: int = 42
) -> Tuple[Dict[int, List[int]], KMeans]:
    """
    Perform k-means clustering on embeddings to group them into topics.

    Args:
        embeddings: A 2D numpy array where each row is an embedding vector
        n_topics: Number of topics (clusters) to create
        random_state: Random seed for reproducibility

    Returns:
        A tuple containing:
        - Dictionary mapping topic IDs to lists of chunk indices
        - Fitted KMeans model for future predictions

    Example:
        ```python
        # Cluster 100 embeddings into 5 topics
        embeddings = np.random.rand(100, 768)  # Example embeddings
        topic_groups, model = perform_topic_clustering(
            embeddings,
            n_topics=5
        )

        # Print chunks in each topic
        for topic_id, chunk_indices in topic_groups.items():
            print(f"Topic {topic_id}: {len(chunk_indices)} chunks")
        ```

    Note:
        The number of embeddings should be >= n_topics for meaningful
        clustering results.
    """
    # Initialize and fit k-means model
    kmeans = KMeans(n_clusters=n_topics, random_state=random_state)
    topics = kmeans.fit_predict(embeddings)

    # Group chunk indices by topic
    topic_groups: Dict[int, List[int]] = {}
    for chunk_idx, topic_id in enumerate(topics):
        if topic_id not in topic_groups:
            topic_groups[topic_id] = []
        topic_groups[topic_id].append(chunk_idx)

    return topic_groups, kmeans


def predict_topic(embedding: np.ndarray, model: KMeans) -> int:
    """
    Predict the topic for a new embedding using a fitted clustering model.

    Args:
        embedding: A 1D numpy array representing the embedding vector
        model: Fitted KMeans clustering model

    Returns:
        Predicted topic ID for the embedding

    Example:
        ```python
        # Get topic for a new chunk
        new_embedding = get_embedding("new_chunk")
        topic_id = predict_topic(new_embedding, model)
        print(f"Chunk belongs to topic {topic_id}")
        ```

    Note:
        The embedding should have the same dimensionality as the
        embeddings used to train the model.
    """
    # Reshape to 2D array if necessary
    if embedding.ndim == 1:
        embedding = embedding.reshape(1, -1)

    return int(model.predict(embedding)[0])
