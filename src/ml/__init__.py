"""Machine Learning package.

This package provides ML-related functionality including:
- Embedding generation with sentence transformers
- Text processing and normalization
- Topic clustering and semantic analysis
- Vector-based semantic search
"""

from typing import TYPE_CHECKING

from .embeddings import EmbeddingGenerator
from .processing import TextProcessor
from .processing.models.chunks import ProcessedChunk
from .search import SemanticSearch
from .service import (
    EMBEDDING_AVAILABLE,
    ServiceInitializationError,
    ServiceNotInitializedError,
    ServiceState,
)

if TYPE_CHECKING:
    from src.core.models.chunks import Chunk
    from src.core.settings import Settings

__all__ = [
    # Main components
    "EmbeddingGenerator",
    "TextProcessor",
    "SemanticSearch",
    "ProcessedChunk",
    # Service states and errors
    "ServiceState",
    "ServiceInitializationError",
    "ServiceNotInitializedError",
    # Feature flags
    "EMBEDDING_AVAILABLE",
]

# Version information
__version__ = "1.0.0"
__author__ = "IndexForge Team"
