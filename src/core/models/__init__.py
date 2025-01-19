"""Core models.

This module provides data models for documents, chunks, references, and document lineage.
"""

from .chunks import Chunk, ChunkMetadata
from .document_operations import (
    BatchOperation,
    DocumentOperationMetadata,
    OperationMetadata,
    OperationResult,
)
from .documents import Document, DocumentMetadata, ProcessingStep
from .lineage import DocumentLineage
from .references import CitationReference, Reference, ReferenceType, SemanticReference
from .settings import Settings
from .types import DocumentStatus, DocumentType

__all__ = [
    # Chunk models
    "Chunk",
    "ChunkMetadata",
    # Document models
    "Document",
    "DocumentMetadata",
    "DocumentStatus",
    "DocumentType",
    "ProcessingStep",
    # Document Operations
    "BatchOperation",
    "DocumentOperationMetadata",
    "OperationMetadata",
    "OperationResult",
    # Lineage models
    "DocumentLineage",
    # Reference models
    "CitationReference",
    "Reference",
    "ReferenceType",
    "SemanticReference",
    # Settings
    "Settings",
]
