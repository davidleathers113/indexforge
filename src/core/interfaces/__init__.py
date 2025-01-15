"""Core interfaces for document processing and storage.

This module provides interfaces for document processing, storage operations,
and reference management.
"""

from .processing import (
    ChunkEmbedder,
    ChunkProcessor,
    ChunkTransformer,
    ChunkValidator,
    TextProcessor,
)
from .reference import ReferenceManager, ReferenceValidator, SemanticReferenceManager
from .storage import ChunkStorage, DocumentStorage, ReferenceStorage, StorageMetrics

__all__ = [
    # Processing interfaces
    "ChunkEmbedder",
    "ChunkProcessor",
    "ChunkTransformer",
    "ChunkValidator",
    "TextProcessor",
    # Reference interfaces
    "ReferenceManager",
    "ReferenceValidator",
    "SemanticReferenceManager",
    # Storage interfaces
    "ChunkStorage",
    "DocumentStorage",
    "ReferenceStorage",
    "StorageMetrics",
]
