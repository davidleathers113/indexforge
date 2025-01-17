"""Machine Learning package.

This package provides ML-related functionality including:
- Embedding generation with sentence transformers
- Text processing and normalization
- Topic clustering and semantic analysis
- Vector-based semantic search
"""

from typing import TYPE_CHECKING

from .embeddings import (
    EMBEDDING_AVAILABLE,
    EmbeddingGenerator,
    ServiceInitializationError,
    ServiceNotInitializedError,
    ServiceState,
)
from .processing import TextProcessor
from .search import SemanticSearch


if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt
    from sentence_transformers import SentenceTransformer

    from src.core.models.chunks import Chunk, ProcessedChunk
    from src.core.settings import Settings

__all__ = [
    # Main components
    "EmbeddingGenerator",
    "TextProcessor",
    "SemanticSearch",
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
