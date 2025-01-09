"""Topic clustering utilities for document organization.

This module provides document clustering capabilities using embeddings and K-means
clustering with automatic cluster size optimization. It includes:

1. Document Clustering:
   - K-means clustering
   - Optimal cluster detection
   - Embedding-based similarity
   - Cluster size management

2. Cluster Analysis:
   - Keyword extraction
   - Cluster labeling
   - Similarity scoring
   - Centroid calculation

3. Performance Optimization:
   - Redis-based caching
   - Batch processing
   - Resource cleanup
   - Error handling

4. Cluster Search:
   - Similar topic finding
   - Vector similarity
   - Cluster ranking
   - Size-aware matching

Usage:
    ```python
    from src.utils.topic_clustering import TopicClusterer
    from src.models.settings import ClusteringConfig

    clusterer = TopicClusterer()

    # Cluster documents
    config = ClusteringConfig(
        min_cluster_size=3,
        max_clusters=10,
        random_state=42
    )
    clustered_docs = clusterer.cluster_documents(documents, config)

    # Find similar topics
    similar = clusterer.find_similar_topics(
        query_vector,
        documents,
        top_k=5
    )
    ```

Note:
    - Uses cosine similarity for matching
    - Caches results for performance
    - Handles document embeddings
    - Auto-scales cluster sizes
"""

import logging
from typing import Dict, List, Optional

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

from src.models.settings import ClusteringConfig
from src.utils.cache_manager import CacheManager, cached_with_retry
from src.utils.text_processing import clean_text

logger = logging.getLogger(__name__)


class TopicClusterer:
    def __init__(
        self,
        cache_host: str = "localhost",
        cache_port: int = 6379,
        cache_ttl: int = 86400,  # 24 hours
    ):
        self.cache_manager = CacheManager(
            host=cache_host, port=cache_port, prefix="cluster", default_ttl=cache_ttl
        )
        self.logger = logging.getLogger(__name__)

    def _get_optimal_clusters(self, embeddings: List[List[float]], config: ClusteringConfig) -> int:
        """Determine optimal number of clusters using elbow method."""
        if len(embeddings) < config.min_cluster_size:
            return 1

        max_clusters = min(config.max_clusters, len(embeddings) // config.min_cluster_size)
        if max_clusters <= 1:
            return 1

        inertias = []
        for k in range(1, max_clusters + 1):
            kmeans = KMeans(
                n_clusters=k,
                random_state=config.random_state,
                n_init=10,  # Explicitly set n_init to avoid FutureWarning
            )
            kmeans.fit(embeddings)
            inertias.append(kmeans.inertia_)

        # Find elbow point
        diffs = np.diff(inertias)
        elbow = np.argmin(diffs) + 1
        return min(elbow, max_clusters)

    def _get_cluster_keywords(
        self, embeddings: List[List[float]], texts: List[str], centroid: List[float], top_k: int = 5
    ) -> List[str]:
        """Extract keywords based on similarity to centroid."""
        # Calculate similarities to centroid
        similarities = cosine_similarity(embeddings, [centroid]).flatten()

        # Get indices of top similar texts
        top_indices = similarities.argsort()[-top_k:][::-1]

        # Extract words from top texts
        keywords = set()
        for idx in top_indices:
            words = clean_text(texts[idx]).split()
            keywords.update(words)

        return list(keywords)[:top_k]

    @cached_with_retry(cache_manager=CacheManager(), key_prefix="clustering", max_attempts=3)
    def cluster_documents(
        self, documents: List[Dict], config: Optional[ClusteringConfig] = None
    ) -> List[Dict]:
        """Cluster documents based on their embeddings."""
        if not documents:
            return []

        if config is None:
            config = ClusteringConfig()

        try:
            # Extract embeddings and texts
            embeddings = [
                doc["embeddings"]["body"] for doc in documents if doc["embeddings"].get("body")
            ]
            if not embeddings:
                self.logger.warning("No embeddings found in documents")
                return documents

            # Determine optimal number of clusters
            n_clusters = self._get_optimal_clusters(embeddings, config)

            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=config.random_state)
            cluster_labels = kmeans.fit_predict(embeddings)

            # Update documents with cluster information
            for i, doc in enumerate(documents):
                if doc["embeddings"].get("body"):
                    cluster_id = int(cluster_labels[i])
                    centroid = kmeans.cluster_centers_[cluster_id]

                    # Get cluster keywords
                    cluster_docs = [
                        d for j, d in enumerate(documents) if cluster_labels[j] == cluster_id
                    ]
                    cluster_texts = [d["content"]["body"] for d in cluster_docs]
                    keywords = self._get_cluster_keywords(embeddings, cluster_texts, centroid)

                    doc["metadata"]["clustering"] = {
                        "cluster_id": cluster_id,
                        "cluster_size": int((cluster_labels == cluster_id).sum()),
                        "keywords": keywords,
                        "similarity_to_centroid": float(
                            cosine_similarity([doc["embeddings"]["body"]], [centroid])[0][0]
                        ),
                    }

            return documents

        except Exception as e:
            self.logger.error(f"Error clustering documents: {str(e)}")
            return documents

    def find_similar_topics(
        self, query_vector: List[float], documents: List[Dict], top_k: int = 5
    ) -> List[Dict]:
        """Find clusters most similar to a query vector."""
        try:
            # Group documents by cluster
            clusters = {}
            for doc in documents:
                cluster_info = doc.get("metadata", {}).get("clustering", {})
                if cluster_info:
                    cluster_id = cluster_info["cluster_id"]
                    if cluster_id not in clusters:
                        clusters[cluster_id] = {"docs": [], "keywords": cluster_info["keywords"]}
                    clusters[cluster_id]["docs"].append(doc)

            # Calculate similarity to each cluster
            cluster_scores = []
            for cluster_id, cluster in clusters.items():
                # Use average embedding of cluster documents
                cluster_embeddings = [
                    doc["embeddings"]["body"]
                    for doc in cluster["docs"]
                    if doc["embeddings"].get("body")
                ]
                if cluster_embeddings:
                    centroid = np.mean(cluster_embeddings, axis=0)
                    similarity = float(cosine_similarity([query_vector], [centroid])[0][0])
                    cluster_scores.append(
                        {
                            "cluster_id": cluster_id,
                            "similarity": similarity,
                            "size": len(cluster["docs"]),
                            "keywords": cluster["keywords"],
                        }
                    )

            # Sort by similarity and return top_k
            cluster_scores.sort(key=lambda x: x["similarity"], reverse=True)
            return cluster_scores[:top_k]

        except Exception as e:
            self.logger.error(f"Error finding similar topics: {str(e)}")
            return []

    def cleanup(self):
        """Clean up resources."""
        try:
            # Clean up cache manager
            if self.cache_manager:
                self.cache_manager.cleanup()

            self.logger.info("TopicClusterer resources cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            raise
