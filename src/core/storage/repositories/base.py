"""Repository base protocols and interfaces.

This module defines the core interfaces for repositories, establishing
a consistent pattern for data access and management across the system.

Key Features:
    - Generic repository interface
    - Type-safe operations
    - Query support
    - Batch operations
    - Error handling
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, Protocol, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterable
    from uuid import UUID

from src.core.models.documents import Document

T = TypeVar("T", bound=Document)


class RepositoryError(Exception):
    """Base exception for repository errors."""


class DocumentNotFoundError(RepositoryError):
    """Raised when a document is not found."""


class DocumentExistsError(RepositoryError):
    """Raised when attempting to create a document that already exists."""


class Repository(Protocol[T]):
    """Protocol defining the interface for repositories."""

    @abstractmethod
    def get(self, doc_id: UUID) -> T:
        """Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            The document

        Raises:
            DocumentNotFoundError: If document not found
        """
        ...

    @abstractmethod
    def create(self, document: T) -> None:
        """Create a new document.

        Args:
            document: Document to create

        Raises:
            DocumentExistsError: If document already exists
        """
        ...

    @abstractmethod
    def update(self, document: T) -> None:
        """Update an existing document.

        Args:
            document: Document to update

        Raises:
            DocumentNotFoundError: If document not found
        """
        ...

    @abstractmethod
    def delete(self, doc_id: UUID) -> None:
        """Delete a document.

        Args:
            doc_id: ID of document to delete

        Raises:
            DocumentNotFoundError: If document not found
        """
        ...

    @abstractmethod
    def exists(self, doc_id: UUID) -> bool:
        """Check if a document exists.

        Args:
            doc_id: Document ID to check

        Returns:
            True if document exists, False otherwise
        """
        ...

    @abstractmethod
    def list_ids(self) -> set[UUID]:
        """Get all document IDs.

        Returns:
            Set of document IDs
        """
        ...


class BaseRepository(ABC, Generic[T]):
    """Base implementation of repository interface."""

    def batch_create(self, documents: Iterable[T]) -> None:
        """Create multiple documents.

        Args:
            documents: Documents to create

        Raises:
            DocumentExistsError: If any document already exists
        """
        for doc in documents:
            self.create(doc)

    def batch_update(self, documents: Iterable[T]) -> None:
        """Update multiple documents.

        Args:
            documents: Documents to update

        Raises:
            DocumentNotFoundError: If any document not found
        """
        for doc in documents:
            self.update(doc)

    def batch_delete(self, doc_ids: Iterable[UUID]) -> None:
        """Delete multiple documents.

        Args:
            doc_ids: IDs of documents to delete

        Raises:
            DocumentNotFoundError: If any document not found
        """
        for doc_id in doc_ids:
            self.delete(doc_id)
