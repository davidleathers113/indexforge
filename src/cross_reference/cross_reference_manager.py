"""
Cross-reference management for document chunks.

This module provides the main CrossReferenceManager class for establishing
and managing various types of relationships between document chunks.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

from .models import ChunkReference, ReferenceType
from .utils.clustering import perform_topic_clustering, predict_topic
from .utils.similarity import compute_cosine_similarities, get_top_similar_indices

logger = logging.getLogger(__name__)


class CrossReferenceManager:
    """
    Manages cross-references between document chunks.

    This class provides functionality for establishing and managing various
    types of relationships between document chunks, including sequential
    ordering, semantic similarity, and topic clustering.

    Attributes:
        similarity_threshold (float): Minimum similarity for semantic refs
        max_semantic_refs (int): Maximum semantic references per chunk
        n_topics (int): Number of topic clusters
        references (Dict[str, List[ChunkReference]]): Stored references
        embeddings (Dict[str, np.ndarray]): Chunk embeddings
        topic_clusters (Optional[KMeans]): Topic clustering model
    """

    def __init__(
        self,
        similarity_threshold: float = 0.8,
        max_semantic_refs: int = 3,
        n_topics: int = 5,
    ):
        """
        Initialize the cross-reference manager.

        Args:
            similarity_threshold: Minimum similarity score (0-1) for semantic refs
            max_semantic_refs: Maximum semantic references per chunk
            n_topics: Number of topics for clustering
        """
        self.similarity_threshold = similarity_threshold
        self.max_semantic_refs = max_semantic_refs
        self.n_topics = n_topics
        self.embeddings: Dict[str, np.ndarray] = {}
        self.references: Dict[str, List[ChunkReference]] = {}
        self.topic_clusters = None
        logger.debug("CrossReferenceManager initialized successfully")

    def add_chunk(self, chunk_id: str, embedding: np.ndarray) -> None:
        """
        Add a chunk and its embedding to the manager.

        Args:
            chunk_id: Unique identifier for the chunk
            embedding: Vector embedding of the chunk content
        """
        if chunk_id not in self.references:
            self.references[chunk_id] = []
        self.embeddings[chunk_id] = embedding

    def establish_sequential_references(self, chunk_ids: List[str]) -> None:
        """
        Establish sequential references between chunks.

        Args:
            chunk_ids: List of chunk IDs in sequential order
        """
        for i in range(len(chunk_ids) - 1):
            current_id = chunk_ids[i]
            next_id = chunk_ids[i + 1]
            self._add_bidirectional_reference(
                current_id,
                next_id,
                ReferenceType.SEQUENTIAL,
            )

    def establish_semantic_references(self) -> None:
        """Establish semantic references between chunks based on similarity."""
        chunk_ids = list(self.embeddings.keys())
        embeddings = np.array([self.embeddings[cid] for cid in chunk_ids])
        logger.debug("Computing similarities for %d chunks", len(chunk_ids))

        # Calculate pairwise similarities
        similarities = compute_cosine_similarities(embeddings)
        logger.debug("Similarity matrix shape: %s", similarities.shape)

        # Create references for each chunk
        for i, chunk_id in enumerate(chunk_ids):
            similar_indices = get_top_similar_indices(
                similarities, index=i, k=self.max_semantic_refs, threshold=self.similarity_threshold
            )
            for j in similar_indices:
                self._add_bidirectional_reference(
                    chunk_id,
                    chunk_ids[j],
                    ReferenceType.SEMANTIC,
                    similarity_score=float(similarities[i, j]),
                )

        logger.debug("Semantic references established successfully")

    def establish_topic_references(self) -> None:
        """Establish topic-based references between chunks."""
        if len(self.embeddings) < self.n_topics:
            logger.warning("Not enough chunks for topic clustering")
            return

        chunk_ids = list(self.embeddings.keys())
        embeddings = np.array([self.embeddings[cid] for cid in chunk_ids])

        # Perform clustering
        topic_groups, self.topic_clusters = perform_topic_clustering(embeddings, self.n_topics)

        # Create references between chunks in same topics
        for topic_id, indices in topic_groups.items():
            chunk_group = [chunk_ids[i] for i in indices]
            for i, source_id in enumerate(chunk_group):
                for target_id in chunk_group[i + 1 :]:
                    self._add_bidirectional_reference(
                        source_id,
                        target_id,
                        ReferenceType.TOPIC,
                        topic_id=topic_id,
                    )

    def get_topic_cluster(self, chunk_id: str) -> Optional[int]:
        """
        Get the topic cluster ID for a chunk.

        Args:
            chunk_id: ID of the chunk to get topic for

        Returns:
            Topic cluster ID or None if not available
        """
        if (
            self.topic_clusters is None
            or chunk_id not in self.embeddings
            or len(self.embeddings) < self.n_topics
        ):
            return None

        return predict_topic(self.embeddings[chunk_id], self.topic_clusters)

    def get_references(
        self,
        chunk_id: str,
        ref_type: Optional[ReferenceType] = None,
        include_metadata: bool = False,
    ) -> List[Tuple[str, ReferenceType, Optional[Dict]]]:
        """
        Get references for a chunk.

        Args:
            chunk_id: ID of the chunk to get references for
            ref_type: Optional filter by reference type
            include_metadata: Whether to include reference metadata

        Returns:
            List of tuples containing:
            - target_id: ID of referenced chunk
            - ref_type: Type of reference
            - metadata: Reference metadata (if include_metadata=True)
        """
        if chunk_id not in self.references:
            return []

        refs = self.references[chunk_id]
        if ref_type:
            refs = [r for r in refs if r.ref_type == ref_type]

        if include_metadata:
            return [(r.target_id, r.ref_type, r.metadata) for r in refs]
        return [(r.target_id, r.ref_type, None) for r in refs]

    def validate_references(self) -> List[str]:
        """
        Validate all references for issues.

        Returns:
            List of error messages, empty if all references are valid
        """
        errors = []

        # Check for orphaned references
        for chunk_id in self.references:
            if chunk_id not in self.embeddings:
                errors.append(f"Orphaned reference source: {chunk_id}")

            for ref in self.references[chunk_id]:
                if ref.target_id not in self.embeddings:
                    errors.append(f"Orphaned reference target: {ref.target_id}")

                # Check for missing back-references
                if ref.target_id in self.references:
                    back_refs = self.references[ref.target_id]
                    has_back_ref = any(
                        back_ref.target_id == chunk_id and back_ref.ref_type == ref.ref_type
                        for back_ref in back_refs
                    )
                    if not has_back_ref:
                        errors.append(
                            f"Missing back-reference: {ref.target_id} -> {chunk_id} ({ref.ref_type})"
                        )

        # Check for circular references
        def check_circular_refs(chunk_id: str, path: List[str]) -> None:
            if chunk_id not in self.references:
                return

            if chunk_id in path:
                cycle = " -> ".join(path[path.index(chunk_id) :] + [chunk_id])
                errors.append(f"Circular reference detected: {cycle}")
                return

            for ref in self.references[chunk_id]:
                check_circular_refs(ref.target_id, path + [chunk_id])

        for chunk_id in self.references:
            check_circular_refs(chunk_id, [])

        return errors

    def _add_bidirectional_reference(
        self,
        source_id: str,
        target_id: str,
        ref_type: ReferenceType,
        similarity_score: Optional[float] = None,
        topic_id: Optional[int] = None,
    ) -> None:
        """
        Add bi-directional references between two chunks.

        Args:
            source_id: ID of the source chunk
            target_id: ID of the target chunk
            ref_type: Type of reference
            similarity_score: Optional similarity score (0-1)
            topic_id: Optional topic cluster ID
        """
        # Forward reference
        self.references[source_id].append(
            ChunkReference(
                source_id=source_id,
                target_id=target_id,
                ref_type=ref_type,
                similarity_score=similarity_score,
                topic_id=topic_id,
            )
        )

        # Backward reference
        self.references[target_id].append(
            ChunkReference(
                source_id=target_id,
                target_id=source_id,
                ref_type=ref_type,
                similarity_score=similarity_score,
                topic_id=topic_id,
            )
        )
