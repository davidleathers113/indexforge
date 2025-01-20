"""Core embedding service implementation.

This module provides the main embedding service interface, delegating specific
operations to specialized components.

Note: This implementation is deprecated. Use src.services.ml.implementations.embedding instead.
"""

from src.core.settings import Settings
from src.services.ml.implementations import EmbeddingService as NewEmbeddingService


class EmbeddingService(NewEmbeddingService):
    """Embedding service for generating chunk embeddings.

    Note: This class is deprecated. Use src.services.ml.implementations.embedding.EmbeddingService instead.
    This class maintains backward compatibility while delegating to the new implementation.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the embedding service.

        Args:
            settings: Application settings
        """
        super().__init__(settings)
        self.add_metadata("warning", "Using deprecated embedding service implementation")
