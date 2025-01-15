"""Core interfaces.

This module defines the core interfaces for document processing,
reference management, and storage operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Generic, List, Optional, Protocol, TypeVar
from uuid import UUID

# Generic type variables
T = TypeVar("T")  # Document type
C = TypeVar("C")  # Chunk type
R = TypeVar("R")  # Reference type


class StorageMetrics(Protocol):
    """Protocol for storage metrics."""

    @abstractmethod
    def get_storage_usage(self) -> Dict[str, int]:
        """Get current storage usage metrics."""
        pass

    @abstractmethod
    def get_operation_counts(self) -> Dict[str, int]:
        """Get operation count metrics."""
        pass


class DocumentStorage(Generic[T], ABC):
    """Interface for document storage operations."""

    @abstractmethod
    def store_document(self, document: T) -> UUID:
        """Store a document and return its ID."""
        pass

    @abstractmethod
    def get_document(self, doc_id: UUID) -> Optional[T]:
        """Retrieve a document by its ID."""
        pass

    @abstractmethod
    def update_document(self, doc_id: UUID, document: T) -> None:
        """Update a document."""
        pass

    @abstractmethod
    def delete_document(self, doc_id: UUID) -> None:
        """Delete a document."""
        pass


class ChunkStorage(Generic[C], ABC):
    """Interface for chunk storage operations."""

    @abstractmethod
    def store_chunk(self, chunk: C) -> UUID:
        """Store a chunk and return its ID."""
        pass

    @abstractmethod
    def get_chunk(self, chunk_id: UUID) -> Optional[C]:
        """Retrieve a chunk by its ID."""
        pass

    @abstractmethod
    def update_chunk(self, chunk_id: UUID, chunk: C) -> None:
        """Update a chunk."""
        pass

    @abstractmethod
    def delete_chunk(self, chunk_id: UUID) -> None:
        """Delete a chunk."""
        pass


class ChunkProcessor(Generic[C], ABC):
    """Interface for chunk processing operations."""

    @abstractmethod
    def process_chunk(self, chunk: C) -> C:
        """Process a chunk and return the processed version."""
        pass


class ChunkEmbedder(Generic[C], ABC):
    """Interface for chunk embedding operations."""

    @abstractmethod
    def embed_chunk(self, chunk: C) -> List[float]:
        """Generate embeddings for a chunk."""
        pass


class ChunkTransformer(Generic[C], ABC):
    """Interface for chunk transformation operations."""

    @abstractmethod
    def transform_chunk(self, chunk: C) -> C:
        """Transform a chunk into a different format."""
        pass


class ChunkValidator(Generic[C], ABC):
    """Interface for chunk validation operations."""

    @abstractmethod
    def validate_chunk(self, chunk: C) -> bool:
        """Validate a chunk's format and content."""
        pass


class ReferenceStorage(Generic[R], ABC):
    """Interface for reference storage operations."""

    @abstractmethod
    def store_reference(self, ref: R) -> None:
        """Store a reference."""
        pass

    @abstractmethod
    def get_references(self, chunk_id: UUID) -> List[R]:
        """Retrieve references for a chunk."""
        pass

    @abstractmethod
    def delete_reference(self, ref: R) -> None:
        """Delete a reference."""
        pass


class ReferenceManager(Generic[R], ABC):
    """Interface for reference management operations."""

    @abstractmethod
    def create_reference(self, source_id: UUID, target_id: UUID, ref_type: str) -> R:
        """Create a new reference between chunks."""
        pass

    @abstractmethod
    def validate_reference(self, ref: R) -> bool:
        """Validate a reference's integrity."""
        pass

    @abstractmethod
    def resolve_reference(self, ref: R) -> Dict[str, UUID]:
        """Resolve a reference to its source and target."""
        pass


class ReferenceValidator(Generic[R], ABC):
    """Interface for reference validation operations."""

    @abstractmethod
    def validate_reference_integrity(self, ref: R) -> bool:
        """Validate the integrity of a reference."""
        pass

    @abstractmethod
    def check_circular_references(self, refs: List[R]) -> bool:
        """Check for circular references in a list of references."""
        pass


class SemanticReferenceManager(ReferenceManager[R], ABC):
    """Interface for semantic reference management operations."""

    @abstractmethod
    def find_semantic_references(self, chunk_id: UUID, threshold: float = 0.7) -> List[R]:
        """Find semantic references for a chunk."""
        pass

    @abstractmethod
    def compute_reference_similarity(self, ref1: R, ref2: R) -> float:
        """Compute similarity between two references."""
        pass
