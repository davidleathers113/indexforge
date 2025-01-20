"""ML embeddings package.

This package provides functionality for generating and managing text embeddings
using transformer models.
"""

from .factory import EmbeddingGeneratorFactory
from .generator import EmbeddingGenerator
from .service import EmbeddingService

__all__ = [
    "EmbeddingService",
    "EmbeddingGeneratorFactory",
    "EmbeddingGenerator",
]
