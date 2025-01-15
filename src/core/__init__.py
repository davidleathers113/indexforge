"""Core package for document processing and storage.

Provides interfaces and base classes for:
- Document processing and storage
- Service lifecycle management
- Text processing and analysis
"""

from .base import BaseService, ServiceStateError
from .interfaces import (
    ChunkEmbedder,
    ChunkProcessor,
    ChunkStorage,
    ChunkTransformer,
    ChunkValidator,
    DocumentStorage,
    ReferenceManager,
    ReferenceStorage,
    ReferenceValidator,
    SemanticReferenceManager,
    StorageMetrics,
    TextProcessor,
)
from .models import (
    Chunk,
    ChunkMetadata,
    CitationReference,
    Document,
    DocumentMetadata,
    DocumentStatus,
    DocumentType,
    ProcessedChunk,
    ProcessingStep,
    Reference,
    ReferenceType,
    SemanticReference,
)
from .utils import (
    calculate_text_similarity,
    chunk_text_by_sentences,
    clean_text,
    compute_cluster_centroids,
    compute_cosine_similarities,
    detect_circular_references,
    find_text_boundaries,
    get_top_similar_indices,
    perform_topic_clustering,
    predict_topic,
    split_into_sentences,
    validate_chunk_references,
    validate_document_relationships,
    validate_reference_integrity,
)

__all__ = [
    # Base classes
    "BaseService",
    "ServiceStateError",
    # Interfaces
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
    # Models
    "Chunk",
    "ChunkMetadata",
    "ProcessedChunk",
    "Document",
    "DocumentMetadata",
    "DocumentStatus",
    "DocumentType",
    "ProcessingStep",
    "CitationReference",
    "Reference",
    "ReferenceType",
    "SemanticReference",
    # Utilities
    "clean_text",
    "split_into_sentences",
    "chunk_text_by_sentences",
    "find_text_boundaries",
    "calculate_text_similarity",
    "compute_cosine_similarities",
    "compute_cluster_centroids",
    "get_top_similar_indices",
    "perform_topic_clustering",
    "predict_topic",
    "detect_circular_references",
    "validate_chunk_references",
    "validate_document_relationships",
    "validate_reference_integrity",
]
