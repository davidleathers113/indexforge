"""Document repository implementation.

This module provides a concrete implementation of the repository interface
for document storage, using JSON files as the storage backend.

Key Features:
    - Type-safe document storage
    - Relationship tracking
    - Metadata management
    - Atomic operations
    - Error handling
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from uuid import UUID

from src.core.models.documents import Document
from src.core.storage.strategies.base import DataNotFoundError, StorageError
from src.core.storage.strategies.json_storage import JsonStorage

from .base import BaseRepository, DocumentExistsError, DocumentNotFoundError, Repository

logger = logging.getLogger(__name__)


class DocumentRepository(BaseRepository[Document], Repository[Document]):
    """Repository implementation for documents."""

    def __init__(self, storage_path: Path) -> None:
        """Initialize document repository.

        Args:
            storage_path: Path to storage directory
        """
        self._storage = JsonStorage(storage_path, Document)
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        """Ensure storage is initialized."""
        try:
            self._storage._ensure_storage_path()
        except StorageError:
            logger.exception("Failed to initialize document storage")
            raise

    def get(self, doc_id: UUID) -> Document:
        """Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            The document

        Raises:
            DocumentNotFoundError: If document not found
        """
        try:
            return self._storage.load(str(doc_id))
        except DataNotFoundError as e:
            raise DocumentNotFoundError(f"Document not found: {doc_id}") from e
        except StorageError:
            logger.exception("Failed to load document %s", doc_id)
            raise

    def create(self, document: Document) -> None:
        """Create a new document.

        Args:
            document: Document to create

        Raises:
            DocumentExistsError: If document already exists
        """
        if self.exists(document.id):
            raise DocumentExistsError(f"Document already exists: {document.id}")

        try:
            self._storage.save(str(document.id), document)
        except StorageError:
            logger.exception("Failed to create document %s", document.id)
            raise

    def update(self, document: Document) -> None:
        """Update an existing document.

        Args:
            document: Document to update

        Raises:
            DocumentNotFoundError: If document not found
        """
        if not self.exists(document.id):
            raise DocumentNotFoundError(f"Document not found: {document.id}")

        try:
            self._storage.save(str(document.id), document)
        except StorageError:
            logger.exception("Failed to update document %s", document.id)
            raise

    def delete(self, doc_id: UUID) -> None:
        """Delete a document.

        Args:
            doc_id: ID of document to delete

        Raises:
            DocumentNotFoundError: If document not found
        """
        try:
            self._storage.delete(str(doc_id))
        except DataNotFoundError as e:
            raise DocumentNotFoundError(f"Document not found: {doc_id}") from e
        except StorageError:
            logger.exception("Failed to delete document %s", doc_id)
            raise

    def exists(self, doc_id: UUID) -> bool:
        """Check if a document exists.

        Args:
            doc_id: Document ID to check

        Returns:
            True if document exists, False otherwise
        """
        return self._storage.exists(str(doc_id))

    def list_ids(self) -> set[UUID]:
        """Get all document IDs.

        Returns:
            Set of document IDs
        """
        try:
            files = list(self._storage.storage_path.glob("*.json"))
            return {UUID(f.stem) for f in files if f.stem != "index" and UUID.is_valid_uuid(f.stem)}
        except Exception as e:
            logger.exception("Failed to list document IDs")
            raise StorageError(f"Failed to list documents: {e}") from e
