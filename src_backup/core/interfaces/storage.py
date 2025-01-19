"""Core storage interfaces.

This module defines the interfaces for storage operations. It provides
protocols for document storage, chunk storage, reference storage, and storage metrics.
"""

from typing import TYPE_CHECKING, Optional, Protocol, TypeVar
from uuid import UUID


if TYPE_CHECKING:
    from src.core.models.chunks import Chunk
    from src.core.models.documents import Document
    from src.core.models.lineage import DocumentLineage
    from src.core.models.references import Reference
    from src.core.settings import Settings

T = TypeVar("T", bound="Document")
C = TypeVar("C", bound="Chunk")
R = TypeVar("R", bound="Reference")


class StorageMetrics(Protocol):
    """Protocol for storage metrics collection."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize storage metrics.

        Args:
            settings: Storage configuration settings
        """
        pass

    def record_operation(self, operation: str, duration: float) -> None:
        """Record a storage operation and its duration.

        Args:
            operation: Name of the storage operation
            duration: Duration of the operation in seconds
        """
        pass

    def get_metrics(self) -> dict[str, list[float]]:
        """Get collected storage metrics.

        Returns:
            Dict[str, List[float]]: Dictionary mapping operation names to lists of durations
        """
        pass


class DocumentStorage(Protocol[T]):
    """Protocol for document storage operations."""

    def store_document(self, document: T) -> UUID:
        """Store a document.

        Args:
            document: Document to store

        Returns:
            UUID: Unique identifier for the stored document
        """
        ...

    def get_document(self, document_id: UUID) -> T:
        """Retrieve a document by ID.

        Args:
            document_id: ID of document to retrieve

        Returns:
            T: Retrieved document
        """
        ...

    def update_document(self, document_id: UUID, document: T) -> None:
        """Update a document.

        Args:
            document_id: ID of document to update
            document: Updated document
        """
        ...

    def delete_document(self, document_id: UUID) -> None:
        """Delete a document.

        Args:
            document_id: ID of document to delete
        """
        ...


class ChunkStorage(Protocol):
    """Protocol for chunk storage operations."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize the chunk storage.

        Args:
            settings (Settings): Application settings
        """
        ...

    def store_chunk(self, chunk: C) -> UUID:
        """Store a chunk.

        Args:
            chunk (C): Chunk to store

        Returns:
            UUID: Generated chunk ID

        Raises:
            ServiceStateError: If storage is not initialized
            ValueError: If chunk is invalid
        """
        ...

    def get_chunk(self, chunk_id: UUID) -> C | None:
        """Get a chunk by ID.

        Args:
            chunk_id (UUID): Chunk ID

        Returns:
            Optional[C]: Chunk if found, None otherwise

        Raises:
            ServiceStateError: If storage is not initialized
        """
        ...

    def update_chunk(self, chunk_id: UUID, chunk: C) -> None:
        """Update a chunk.

        Args:
            chunk_id (UUID): Chunk ID
            chunk (C): Updated chunk

        Raises:
            ServiceStateError: If storage is not initialized
            ValueError: If chunk is invalid
            KeyError: If chunk does not exist
        """
        ...

    def delete_chunk(self, chunk_id: UUID) -> None:
        """Delete a chunk.

        Args:
            chunk_id (UUID): Chunk ID

        Raises:
            ServiceStateError: If storage is not initialized
            KeyError: If chunk does not exist
        """
        ...


class ReferenceStorage(Protocol):
    """Protocol for reference storage operations."""

    def __init__(self, settings: "Settings") -> None:
        """Initialize the reference storage.

        Args:
            settings (Settings): Application settings
        """
        ...

    def store_reference(self, ref: R) -> None:
        """Store a reference.

        Args:
            ref (R): Reference to store

        Raises:
            ServiceStateError: If storage is not initialized
            ValueError: If reference is invalid
        """
        ...

    def get_references(self, chunk_id: UUID) -> list[R]:
        """Get references for a chunk.

        Args:
            chunk_id (UUID): Chunk ID

        Returns:
            List[R]: List of references associated with the chunk

        Raises:
            ServiceStateError: If storage is not initialized
        """
        ...

    def delete_reference(self, ref: R) -> None:
        """Delete a reference.

        Args:
            ref (R): Reference to delete

        Raises:
            ServiceStateError: If storage is not initialized
            KeyError: If reference does not exist
        """
        ...


class LineageStorage(Protocol):
    """Protocol for document lineage storage operations."""

    def get_lineage(self, doc_id: str) -> Optional["DocumentLineage"]:
        """Retrieve lineage information for a document.

        Args:
            doc_id: ID of the document to retrieve

        Returns:
            DocumentLineage if found, None otherwise
        """
        ...

    def save_lineage(self, lineage: "DocumentLineage") -> None:
        """Save lineage information for a document.

        Args:
            lineage: The document lineage to save
        """
        ...

    def delete_lineage(self, doc_id: str) -> None:
        """Delete lineage information for a document.

        Args:
            doc_id: ID of the document to delete
        """
        ...
