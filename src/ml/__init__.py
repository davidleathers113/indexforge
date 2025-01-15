"""Machine Learning package.

This package provides ML-related functionality including:
- Embedding generation
- Text processing
- Topic clustering
- Semantic search
"""

from .embeddings import EmbeddingGenerator
from .processing import TextProcessor
from .search import SemanticSearch

__all__ = ["EmbeddingGenerator", "TextProcessor", "SemanticSearch"]
