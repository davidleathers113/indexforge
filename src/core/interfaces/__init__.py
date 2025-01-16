"""Core interfaces for document processing and storage.

This module provides interfaces for document processing, storage operations,
and reference management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .processing import (
    ChunkEmbedder,
    ChunkProcessor,
    ChunkTransformer,
    ChunkValidator,
    TextProcessor,
)
from .reference import ReferenceManager, ReferenceValidator, SemanticReferenceManager
from .search import VectorSearcher
from .storage import ChunkStorage, DocumentStorage, ReferenceStorage, StorageMetrics


if TYPE_CHECKING:
    from ..models.chunks import Chunk, ProcessedChunk
    from ..models.documents import Document
    from ..models.references import Reference

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
    # Search interfaces
    "VectorSearcher",
    # Storage interfaces
    "ChunkStorage",
    "DocumentStorage",
    "ReferenceStorage",
    "StorageMetrics",
    # Type exports
    "Chunk",
    "ProcessedChunk",
    "Document",
    "Reference",
]
