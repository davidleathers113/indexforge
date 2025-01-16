"""Semantic search module.

This module provides functionality for semantic search operations using
vector embeddings and cosine similarity.
"""

from typing import TYPE_CHECKING, Any, cast

try:
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from src.core import BaseService, Chunk, VectorSearcher
from src.ml.processing.models.service import (
    ServiceInitializationError,
    ServiceState,
    ServiceStateError,
)

if TYPE_CHECKING:
    from src.core.settings import Settings
    from src.ml.embeddings import EmbeddingGenerator
    from src.services.weaviate import WeaviateClient


class SemanticSearch(BaseService, VectorSearcher):
    """Semantic search implementation using vector embeddings."""

    def __init__(
        self,
        vector_db: "WeaviateClient",
        embedding_generator: "EmbeddingGenerator",
        settings: "Settings",
    ) -> None:
        """Initialize the semantic search.

        Args:
            vector_db: Vector database client
            embedding_generator: Embedding generator instance
            settings: Application settings

        Raises:
            ValueError: If required settings are missing
            ImportError: If scikit-learn is not available
        """
        if not settings.min_similarity_score:
            raise ValueError("min_similarity_score setting is required")
        if not settings.max_search_results:
            raise ValueError("max_search_results setting is required")

        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for semantic search")

        BaseService.__init__(self)
        VectorSearcher.__init__(self, settings)
        self.vector_db = vector_db
        self.embedding_generator = embedding_generator
        self._settings = settings

    async def initialize(self) -> None:
        """Initialize search service.

        Raises:
            ServiceInitializationError: If initialization fails
        """
        self._transition_state(ServiceState.INITIALIZING)
        try:
            # Verify vector DB connection
            await self.vector_db.health_check()
            # Verify embedding generator
            if not self.embedding_generator.is_initialized:
                await self.embedding_generator.initialize()

            self._initialized = True
            self._transition_state(ServiceState.RUNNING)
            self.add_metadata("vector_db_type", self.vector_db.__class__.__name__)
            self.add_metadata("embedding_model", self._settings.embedding_model)
        except Exception as e:
            self._transition_state(ServiceState.ERROR)
            raise ServiceInitializationError(f"Failed to initialize search service: {e!s}") from e

    async def cleanup(self) -> None:
        """Clean up resources.

        Raises:
            ServiceStateError: If cleanup fails
        """
        self._transition_state(ServiceState.STOPPING)
        try:
            self._initialized = False
            self._transition_state(ServiceState.STOPPED)
        except Exception as e:
            self._transition_state(ServiceState.ERROR)
            raise ServiceStateError(f"Failed to cleanup resources: {e!s}") from e

    def validate_query(self, query: str) -> list[str]:
        """Validate a search query.

        Args:
            query: Query to validate

        Returns:
            List of validation error messages, empty if valid

        Raises:
            TypeError: If query is not a string
        """
        if not isinstance(query, str):
            raise TypeError("Query must be a string")

        errors = []
        if not query.strip():
            errors.append("Query is empty or whitespace")
        if len(query) < 3:
            errors.append("Query must be at least 3 characters long")
        if len(query) > self._settings.max_query_length:
            errors.append(f"Query exceeds maximum length of {self._settings.max_query_length}")

        return errors

    def search(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> list[tuple[Chunk, float]]:
        """Perform semantic search.

        Args:
            query: Search query text
            limit: Maximum number of results to return
            min_score: Minimum similarity score threshold
            metadata: Optional search metadata

        Returns:
            List of tuples containing (chunk, score) where:
                - chunk: The matching chunk
                - score: Similarity score between 0 and 1

        Raises:
            ServiceStateError: If searcher is not initialized
            ValueError: If query is empty or parameters are invalid
            TypeError: If query is not a string
        """
        # Validate state and inputs
        self._check_running()
        validation_errors = self.validate_query(query)
        if validation_errors:
            raise ValueError(f"Invalid query: {'; '.join(validation_errors)}")

        if limit <= 0:
            raise ValueError("limit must be positive")
        if not 0 <= min_score <= 1:
            raise ValueError("min_score must be between 0 and 1")

        # Add search metadata if provided
        if metadata:
            self.add_metadata("last_search_metadata", metadata)
            self.add_metadata("last_search_limit", limit)
            self.add_metadata("last_search_min_score", min_score)

        # Generate query embedding
        query_chunk = Chunk(content=query)
        query_embedding = self.embedding_generator.embed_chunk(query_chunk, metadata=metadata)

        # Search vector database
        results = self.vector_db.search(
            vector=query_embedding, limit=limit, min_score=min_score, metadata=metadata
        )

        # Convert results to proper type
        return [(cast("Chunk", doc), score) for doc, score in results]

    def find_similar(
        self,
        text: str,
        texts: list[str],
        limit: int | None = None,
        min_score: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> list[tuple[str, float]]:
        """Find similar texts from a list.

        Args:
            text: Query text to find similar matches for
            texts: List of texts to search through
            limit: Maximum number of results to return (None for all)
            min_score: Minimum similarity score threshold
            metadata: Optional similarity search metadata

        Returns:
            List of tuples containing (similar_text, score) where:
                - similar_text: The matching text
                - score: Similarity score between 0 and 1

        Raises:
            ServiceStateError: If searcher is not initialized
            ValueError: If text is empty or parameters are invalid
            TypeError: If inputs are not strings
        """
        # Validate state and inputs
        self._check_running()
        validation_errors = self.validate_query(text)
        if validation_errors:
            raise ValueError(f"Invalid query text: {'; '.join(validation_errors)}")

        if not isinstance(texts, list):
            raise TypeError("texts must be a list of strings")
        if not all(isinstance(t, str) for t in texts):
            raise TypeError("all texts must be strings")
        if not texts:
            raise ValueError("texts list is empty")
        if min_score < 0 or min_score > 1:
            raise ValueError("min_score must be between 0 and 1")
        if limit is not None and limit <= 0:
            raise ValueError("limit must be positive if specified")

        # Add search metadata if provided
        if metadata:
            self.add_metadata("last_similarity_search_metadata", metadata)
            self.add_metadata("last_similarity_search_corpus_size", len(texts))

        # Generate embeddings
        query_chunk = Chunk(content=text)
        query_embedding = self.embedding_generator.embed_chunk(query_chunk, metadata=metadata)

        corpus_chunks = [Chunk(content=t) for t in texts]
        corpus_embeddings = [
            self.embedding_generator.embed_chunk(chunk, metadata=metadata)
            for chunk in corpus_chunks
        ]

        # Calculate similarities
        similarities = cosine_similarity([query_embedding], corpus_embeddings)[0]

        # Filter and sort results
        results = []
        for idx, score in enumerate(similarities):
            if score >= min_score:
                results.append((texts[idx], float(score)))

        results.sort(key=lambda x: x[1], reverse=True)

        if limit:
            results = results[:limit]

        return results
