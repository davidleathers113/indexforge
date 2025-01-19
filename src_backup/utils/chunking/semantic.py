"""Semantic relationship detection for text chunks.

This module provides functionality for detecting semantic relationships between
chunks using embeddings and content similarity analysis. It supports automatic
reference generation based on semantic similarity and topic mapping.
"""

from dataclasses import dataclass
from uuid import UUID

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from .references import ReferenceManager, ReferenceType


@dataclass
class SemanticConfig:
    """Configuration for semantic relationship detection."""

    similarity_threshold: float = 0.7  # Minimum similarity score to create a reference
    max_similar_chunks: int = 5  # Maximum number of similar chunks to reference
    min_context_score: float = 0.5  # Minimum score for context relationships
    embedding_model: str = "text-embedding-3-small"  # Model to use for embeddings
    cache_embeddings: bool = True  # Whether to cache chunk embeddings

    def __post_init__(self):
        """Validate configuration parameters."""
        if not 0 <= self.similarity_threshold <= 1:
            raise ValueError("similarity_threshold must be between 0 and 1")
        if self.max_similar_chunks < 1:
            raise ValueError("max_similar_chunks must be positive")
        if not 0 <= self.min_context_score <= 1:
            raise ValueError("min_context_score must be between 0 and 1")


class SemanticProcessor:
    """Processes semantic relationships between chunks."""

    def __init__(
        self,
        ref_manager: ReferenceManager,
        config: SemanticConfig | None = None,
        embedding_cache: dict[UUID, np.ndarray] | None = None,
    ):
        """Initialize the semantic processor.

        Args:
            ref_manager: Reference manager to use for creating references
            config: Optional configuration for semantic processing
            embedding_cache: Optional cache of pre-computed embeddings
        """
        self.ref_manager = ref_manager
        self.config = config or SemanticConfig()
        self._embedding_cache = embedding_cache or {}
        self._initialize_embedding_model()

    def _initialize_embedding_model(self):
        """Initialize the embedding model."""
        try:
            import openai

            self._get_embedding = (
                lambda text: openai.embeddings.create(model=self.config.embedding_model, input=text)
                .data[0]
                .embedding
            )
        except ImportError:
            raise ImportError("OpenAI package is required for semantic processing")

    def get_chunk_embedding(self, chunk_id: UUID) -> np.ndarray:
        """Get the embedding for a chunk, using cache if available."""
        if chunk_id in self._embedding_cache:
            return self._embedding_cache[chunk_id]

        chunk = self.ref_manager._chunks.get(chunk_id)
        if not chunk:
            raise ValueError(f"Chunk {chunk_id} does not exist")

        embedding = np.array(self._get_embedding(chunk.content))
        if self.config.cache_embeddings:
            self._embedding_cache[chunk_id] = embedding

        return embedding

    def compute_similarity(self, chunk_id1: UUID, chunk_id2: UUID) -> float:
        """Compute cosine similarity between two chunks."""
        emb1 = self.get_chunk_embedding(chunk_id1)
        emb2 = self.get_chunk_embedding(chunk_id2)
        return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))

    def find_similar_chunks(self, chunk_id: UUID) -> list[tuple[UUID, float]]:
        """Find chunks similar to the given chunk.

        Args:
            chunk_id: ID of the chunk to find similar chunks for

        Returns:
            List of (chunk_id, similarity_score) tuples, sorted by similarity
        """
        target_embedding = self.get_chunk_embedding(chunk_id)
        similarities = []

        for other_id in self.ref_manager._chunks:
            if other_id == chunk_id:
                continue

            other_embedding = self.get_chunk_embedding(other_id)
            similarity = float(
                np.dot(target_embedding, other_embedding)
                / (np.linalg.norm(target_embedding) * np.linalg.norm(other_embedding))
            )
            if similarity >= self.config.similarity_threshold:
                similarities.append((other_id, similarity))

        # Sort by similarity score and limit to max_similar_chunks
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[: self.config.max_similar_chunks]

    def detect_semantic_relationships(
        self, chunk_id: UUID
    ) -> dict[ReferenceType, list[tuple[UUID, float]]]:
        """Detect semantic relationships for a chunk.

        Args:
            chunk_id: ID of the chunk to analyze

        Returns:
            Dictionary mapping reference types to lists of (chunk_id, score) tuples
        """
        relationships = {
            ReferenceType.SIMILAR: [],
            ReferenceType.CONTEXT: [],
            ReferenceType.RELATED: [],
        }

        similar_chunks = self.find_similar_chunks(chunk_id)
        for other_id, similarity in similar_chunks:
            if similarity >= self.config.similarity_threshold:
                relationships[ReferenceType.SIMILAR].append((other_id, similarity))
            elif similarity >= self.config.min_context_score:
                relationships[ReferenceType.CONTEXT].append((other_id, similarity))
            else:
                relationships[ReferenceType.RELATED].append((other_id, similarity))

        return relationships

    def create_semantic_references(self, chunk_id: UUID) -> list[tuple[UUID, ReferenceType, float]]:
        """Create semantic references for a chunk.

        Args:
            chunk_id: ID of the chunk to create references for

        Returns:
            List of (chunk_id, reference_type, similarity_score) tuples for created references
        """
        created_refs = []
        relationships = self.detect_semantic_relationships(chunk_id)

        for ref_type, chunks in relationships.items():
            for other_id, score in chunks:
                # Add reference with metadata including similarity score
                self.ref_manager.add_reference(
                    chunk_id,
                    other_id,
                    ref_type,
                    metadata={"similarity_score": score},
                    bidirectional=True,
                )
                created_refs.append((other_id, ref_type, score))

        return created_refs

    def analyze_topic_relationships(
        self, chunk_ids: set[UUID], num_topics: int = 5
    ) -> dict[str, set[UUID]]:
        """Group chunks by topic similarity using k-means clustering.

        Args:
            chunk_ids: Set of chunk IDs to analyze
            num_topics: Number of topics to identify (default: 5)

        Returns:
            Dictionary mapping topic labels to sets of chunk IDs
        """
        if not chunk_ids:
            return {}

        # Get embeddings for all chunks
        chunk_embeddings = []
        valid_chunk_ids = []
        for chunk_id in chunk_ids:
            try:
                embedding = self.get_chunk_embedding(chunk_id)
                chunk_embeddings.append(embedding)
                valid_chunk_ids.append(chunk_id)
            except ValueError:
                continue  # Skip invalid chunks

        if not chunk_embeddings:
            return {}

        # Convert to numpy array for clustering
        embeddings_array = np.array(chunk_embeddings)

        # Perform k-means clustering
        kmeans = KMeans(n_clusters=min(num_topics, len(valid_chunk_ids)), random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings_array)

        # Extract representative terms for each cluster using TF-IDF
        chunk_texts = [self.ref_manager._chunks[chunk_id].content for chunk_id in valid_chunk_ids]
        vectorizer = TfidfVectorizer(max_features=10, stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(chunk_texts)
        feature_names = vectorizer.get_feature_names_out()

        # Create topic labels based on top terms
        topic_terms = {}
        for cluster_id in range(kmeans.n_clusters_):
            cluster_docs = tfidf_matrix[cluster_labels == cluster_id]
            if cluster_docs.shape[0] > 0:
                avg_tfidf = cluster_docs.mean(axis=0).A1
                top_term_indices = avg_tfidf.argsort()[-3:][::-1]  # Get top 3 terms
                topic_terms[cluster_id] = ", ".join(feature_names[i] for i in top_term_indices)

        # Group chunks by topic
        topics = {}
        for chunk_id, cluster_id in zip(valid_chunk_ids, cluster_labels, strict=False):
            topic_label = f"Topic {cluster_id + 1}: {topic_terms[cluster_id]}"
            if topic_label not in topics:
                topics[topic_label] = set()
            topics[topic_label].add(chunk_id)

        return topics
