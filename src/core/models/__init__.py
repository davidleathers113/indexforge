"""Core models.

This module provides data models for documents, chunks, references, and document lineage.
"""

from src.core.tracking.models.lineage import DocumentLineage

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
    # Lineage models
    "DocumentLineage",
    # Reference models
    "CitationReference",
    "Reference",
    "ReferenceType",
    "SemanticReference",
]
