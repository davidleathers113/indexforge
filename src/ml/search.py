"""Semantic search module.

This module provides functionality for semantic search operations using
vector embeddings.
"""

from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Tuple

try:
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from src.core import BaseService, ServiceStateError
from src.core.interfaces import VectorSearcher

if TYPE_CHECKING:
    from src.core.settings import Settings
    from src.ml.embeddings import EmbeddingGenerator
    from src.services.weaviate import WeaviateClient


class ServiceState(Enum):
    """Service lifecycle states."""

    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ServiceInitializationError(ServiceStateError):
    """Raised when service initialization fails."""

    pass


class ServiceNotInitializedError(ServiceStateError):
    """Raised when attempting to use an uninitialized service."""

    pass


class SemanticSearch(BaseService, VectorSearcher):
    """Handles semantic search operations."""

    def __init__(
        self,
        vector_db: "WeaviateClient",
        embedding_generator: "EmbeddingGenerator",
        settings: "Settings",
    ):
        """Initialize the semantic search.

        Args:
            vector_db: Vector database client
            embedding_generator: Embedding generator instance
            settings: Application settings
        """
        BaseService.__init__(self)
        VectorSearcher.__init__(self, settings)
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for semantic search")
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
            self._initialized = True
            self._transition_state(ServiceState.RUNNING)
        except Exception as e:
            self._transition_state(ServiceState.ERROR)
            raise ServiceInitializationError(
                f"Failed to initialize search service: {str(e)}"
            ) from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._transition_state(ServiceState.STOPPING)
        try:
            self._initialized = False
            self._transition_state(ServiceState.STOPPED)
        except Exception as e:
            self._transition_state(ServiceState.ERROR)
            raise ServiceStateError(f"Failed to cleanup resources: {str(e)}") from e

    def search(
        self, query: str, limit: int = 10, min_score: float = 0.0
    ) -> List[Tuple[dict, float]]:
        """Perform semantic search.

        Args:
            query: Search query text
            limit: Maximum number of results to return
            min_score: Minimum similarity score threshold

        Returns:
            List of tuples containing (document, score)

        Raises:
            ServiceNotInitializedError: If service is not initialized
        """
        self._check_running()

        # Generate query embedding
        query_embedding = self.embedding_generator.embed_chunk({"content": query})

        # Search vector database
        results = self.vector_db.search(vector=query_embedding, limit=limit, min_score=min_score)

        return results

    def find_similar(
        self, text: str, texts: List[str], limit: Optional[int] = None, min_score: float = 0.0
    ) -> List[Tuple[str, float]]:
        """Find similar texts from a list.

        Args:
            text: Query text to find similar matches for
            texts: List of texts to search through
            limit: Maximum number of results to return
            min_score: Minimum similarity score threshold

        Returns:
            List of tuples containing (similar_text, score)

        Raises:
            ServiceNotInitializedError: If service is not initialized
        """
        self._check_running()

        # Generate embeddings
        query_embedding = self.embedding_generator.embed_chunk({"content": text})
        corpus_embeddings = [self.embedding_generator.embed_chunk({"content": t}) for t in texts]

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
