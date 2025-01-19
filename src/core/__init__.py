"""Core package for document processing and storage.

Provides interfaces and base classes for:
- Document processing and storage
- Service lifecycle management
- Text processing and analysis
- Document lineage validation
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
    VectorSearcher,
)
from .models import (
    Chunk,
    ChunkMetadata,
    CitationReference,
    Document,
    DocumentMetadata,
    DocumentStatus,
    DocumentType,
    ProcessingStep,
    Reference,
    ReferenceType,
    SemanticReference,
)
from .tracking.validation import (
    ChunkReferenceValidator,
    CircularDependencyValidator,
    CompositeValidator,
    RelationshipValidator,
    ValidationError,
    ValidationStrategy,
)
from .utils.similarity import (
    calculate_text_similarity,
    compute_cluster_centroids,
    compute_cosine_similarities,
    get_top_similar_indices,
)
from .utils.text import (
    chunk_text_by_sentences,
    clean_text,
    find_text_boundaries,
    split_into_sentences,
)
from .utils.validation import (
    detect_circular_references,
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
    "VectorSearcher",
    # Models
    "Chunk",
    "ChunkMetadata",
    "Document",
    "DocumentMetadata",
    "DocumentStatus",
    "DocumentType",
    "ProcessingStep",
    "CitationReference",
    "Reference",
    "ReferenceType",
    "SemanticReference",
    # Validation
    "ValidationStrategy",
    "ValidationError",
    "ChunkReferenceValidator",
    "CircularDependencyValidator",
    "RelationshipValidator",
    "CompositeValidator",
    # Utilities
    "clean_text",
    "split_into_sentences",
    "chunk_text_by_sentences",
    "find_text_boundaries",
    "calculate_text_similarity",
    "compute_cosine_similarities",
    "compute_cluster_centroids",
    "get_top_similar_indices",
    "detect_circular_references",
    "validate_chunk_references",
    "validate_document_relationships",
    "validate_reference_integrity",
]
