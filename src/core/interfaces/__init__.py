"""Core interfaces for document processing and storage.

This module provides interfaces for document processing, storage operations,
and reference management.
"""

from __future__ import annotations

from .cache import CacheService
from .processing import (
    ChunkEmbedder,
    ChunkProcessor,
    ChunkTransformer,
    ChunkValidator,
    TextProcessor,
)
from .reference import ReferenceManager, ReferenceValidator, SemanticReferenceManager
from .search import VectorSearcher, VectorService
from .storage import ChunkStorage, DocumentStorage, ReferenceStorage, StorageMetrics


__all__ = [
    "CacheService",
    "ChunkEmbedder",
    "ChunkProcessor",
    "ChunkStorage",
    "ChunkTransformer",
    "ChunkValidator",
    "DocumentStorage",
    "ReferenceManager",
    "ReferenceStorage",
    "ReferenceValidator",
    "SemanticReferenceManager",
    "StorageMetrics",
    "TextProcessor",
    "VectorSearcher",
    "VectorService",
]
