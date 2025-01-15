"""Core models.

This module provides data models for documents, chunks, and references.
"""

from .chunks import Chunk, ChunkMetadata, ProcessedChunk
from .documents import Document, DocumentMetadata, DocumentStatus, DocumentType, ProcessingStep
from .references import CitationReference, Reference, ReferenceType, SemanticReference

__all__ = [
    # Chunk models
    "Chunk",
    "ChunkMetadata",
    "ProcessedChunk",
    # Document models
    "Document",
    "DocumentMetadata",
    "DocumentStatus",
    "DocumentType",
    "ProcessingStep",
    # Reference models
    "CitationReference",
    "Reference",
    "ReferenceType",
    "SemanticReference",
]
