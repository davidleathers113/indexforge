"""Core storage interfaces.

This module defines the interfaces for storage operations. It provides
abstract base classes for document storage, chunk storage, and reference
storage.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Protocol, TypeVar
from uuid import UUID

from src.core.models.chunks import Chunk
from src.core.models.documents import Document
from src.core.models.references import Reference

T = TypeVar("T", bound=Document)
C = TypeVar("C", bound=Chunk)


class StorageMetrics(Protocol):
    """Protocol for storage metrics."""

    def get_storage_usage(self) -> Dict[str, int]:
        """Get storage usage metrics.

        Returns:
            Dictionary of storage metrics
        """
        ...

    def get_operation_counts(self) -> Dict[str, int]:
        """Get operation count metrics.

        Returns:
            Dictionary of operation counts
        """
        ...


class DocumentStorage(ABC):
    """Interface for document storage."""

    @abstractmethod
    def store_document(self, document: T) -> UUID:
        """Store a document.

        Args:
            document: Document to store

        Returns:
            Document ID
        """
        pass

    @abstractmethod
    def get_document(self, doc_id: UUID) -> Optional[T]:
        """Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document if found, None otherwise
        """
        pass

    @abstractmethod
    def update_document(self, doc_id: UUID, document: T) -> None:
        """Update a document.

        Args:
            doc_id: Document ID
            document: Updated document
        """
        pass

    @abstractmethod
    def delete_document(self, doc_id: UUID) -> None:
        """Delete a document.

        Args:
            doc_id: Document ID
        """
        pass


class ChunkStorage(ABC):
    """Interface for chunk storage."""

    @abstractmethod
    def store_chunk(self, chunk: C) -> UUID:
        """Store a chunk.

        Args:
            chunk: Chunk to store

        Returns:
            Chunk ID
        """
        pass

    @abstractmethod
    def get_chunk(self, chunk_id: UUID) -> Optional[C]:
        """Get a chunk by ID.

        Args:
            chunk_id: Chunk ID

        Returns:
            Chunk if found, None otherwise
        """
        pass

    @abstractmethod
    def update_chunk(self, chunk_id: UUID, chunk: C) -> None:
        """Update a chunk.

        Args:
            chunk_id: Chunk ID
            chunk: Updated chunk
        """
        pass

    @abstractmethod
    def delete_chunk(self, chunk_id: UUID) -> None:
        """Delete a chunk.

        Args:
            chunk_id: Chunk ID
        """
        pass


class ReferenceStorage(ABC):
    """Interface for reference storage."""

    @abstractmethod
    def store_reference(self, ref: Reference) -> None:
        """Store a reference.

        Args:
            ref: Reference to store
        """
        pass

    @abstractmethod
    def get_references(self, chunk_id: UUID) -> List[Reference]:
        """Get references for a chunk.

        Args:
            chunk_id: Chunk ID

        Returns:
            List of references
        """
        pass

    @abstractmethod
    def delete_reference(self, ref: Reference) -> None:
        """Delete a reference.

        Args:
            ref: Reference to delete
        """
        pass
