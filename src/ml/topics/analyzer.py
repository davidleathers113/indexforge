"""Topic clustering utilities.

This module provides utilities for clustering and analyzing document topics using
embeddings and machine learning techniques.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from .exceptions import ClusteringError, ConfigurationError, InsufficientDataError

logger = logging.getLogger(__name__)


@dataclass
class ClusteringConfig:
    """Configuration for topic clustering."""

    min_clusters: int = 2
    max_clusters: int = 10
    random_state: int = 42
    n_init: int = 10
    max_iter: int = 300

    def validate(self) -> None:
        """Validate configuration parameters.

        Raises:
            ConfigurationError: If parameters are invalid
        """
        if self.min_clusters < 2:
            raise ConfigurationError("min_clusters must be at least 2")
        if self.max_clusters < self.min_clusters:
            raise ConfigurationError("max_clusters must be greater than min_clusters")
        if self.n_init < 1:
            raise ConfigurationError("n_init must be positive")
        if self.max_iter < 1:
            raise ConfigurationError("max_iter must be positive")


class TopicClusterer:
    """Document topic clustering and analysis."""

    def __init__(self) -> None:
        """Initialize the topic clusterer."""
        self._models: Dict[int, KMeans] = {}
        logger.info("Initialized TopicClusterer")

    def _get_optimal_clusters(
        self, embeddings: np.ndarray, config: ClusteringConfig
    ) -> Tuple[int, float]:
        """Find the optimal number of clusters using silhouette analysis.

        Args:
            embeddings: Document embeddings matrix
            config: Clustering configuration

        Returns:
            Tuple of (optimal number of clusters, best silhouette score)

        Raises:
            InsufficientDataError: If not enough samples for clustering
            ClusteringError: If clustering fails
        """
        if len(embeddings) < config.min_clusters:
            raise InsufficientDataError(
                f"Not enough samples ({len(embeddings)}) for clustering. "
                f"Minimum required: {config.min_clusters}"
            )

        config.validate()
        best_score = -1
        best_n_clusters = config.min_clusters

        for n_clusters in range(config.min_clusters, min(config.max_clusters + 1, len(embeddings))):
            try:
                model = KMeans(
                    n_clusters=n_clusters,
                    random_state=config.random_state,
                    n_init=config.n_init,
                    max_iter=config.max_iter,
                )
                labels = model.fit_predict(embeddings)
                score = silhouette_score(embeddings, labels)

                if score > best_score:
                    best_score = score
                    best_n_clusters = n_clusters
                    self._models[n_clusters] = model

                logger.debug(
                    "Clusters: %d, Silhouette score: %.3f",
                    n_clusters,
                    score,
                )
            except Exception as e:
                logger.exception("Error during clustering with n=%d: %s", n_clusters, str(e))
                raise ClusteringError(f"Failed to cluster with n={n_clusters}: {str(e)}") from e

        logger.info(
            "Optimal clusters: %d, Silhouette score: %.3f",
            best_n_clusters,
            best_score,
        )
        return best_n_clusters, best_score

    def cluster_documents(
        self,
        embeddings: np.ndarray,
        texts: Optional[List[str]] = None,
        config: Optional[ClusteringConfig] = None,
    ) -> Dict[str, any]:
        """Cluster documents and analyze topics.

        Args:
            embeddings: Document embeddings matrix
            texts: Optional list of document texts for keyword extraction
            config: Optional clustering configuration

        Returns:
            Dictionary containing clustering results:
            - n_clusters: Number of clusters found
            - labels: Cluster labels for each document
            - silhouette_score: Quality metric for clustering
            - cluster_sizes: Number of documents in each cluster
            - cluster_centers: Centroid vectors for each cluster

        Raises:
            InsufficientDataError: If not enough samples for clustering
            ConfigurationError: If clustering configuration is invalid
            ClusteringError: If clustering fails
        """
        if embeddings.ndim != 2:
            raise ConfigurationError("Embeddings must be a 2D matrix")

        if texts is not None and len(texts) != len(embeddings):
            raise ConfigurationError("Number of texts must match number of embeddings")

        config = config or ClusteringConfig()

        try:
            n_clusters, score = self._get_optimal_clusters(embeddings, config)
            model = self._models[n_clusters]
            labels = model.labels_

            # Get cluster sizes
            unique_labels, counts = np.unique(labels, return_counts=True)
            cluster_sizes = dict(zip(unique_labels, counts))

            result = {
                "n_clusters": n_clusters,
                "labels": labels.tolist(),
                "silhouette_score": float(score),
                "cluster_sizes": cluster_sizes,
                "cluster_centers": model.cluster_centers_.tolist(),
            }

            logger.info(
                "Clustered %d documents into %d topics",
                len(embeddings),
                n_clusters,
            )
            return result

        except Exception as e:
            logger.exception("Failed to cluster documents: %s", str(e))
            raise ClusteringError(f"Failed to cluster documents: {str(e)}") from e

    def predict_cluster(self, embedding: np.ndarray, n_clusters: int) -> int:
        """Predict the cluster for a new document embedding.

        Args:
            embedding: Document embedding vector
            n_clusters: Number of clusters to use

        Returns:
            Predicted cluster index

        Raises:
            ConfigurationError: If the model for n_clusters doesn't exist
            ClusteringError: If prediction fails
        """
        if n_clusters not in self._models:
            raise ConfigurationError(f"No model available for {n_clusters} clusters")

        try:
            model = self._models[n_clusters]
            return int(model.predict(embedding.reshape(1, -1))[0])
        except Exception as e:
            logger.exception("Failed to predict cluster: %s", str(e))
            raise ClusteringError(f"Failed to predict cluster: {str(e)}") from e
