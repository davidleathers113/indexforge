"""Lineage repository implementation.

This module provides a concrete implementation of the repository interface
for document lineage storage, using JSON files as the storage backend.

Key Features:
    - Document lineage tracking
    - Relationship management
    - History tracking
    - Query capabilities
    - Atomic operations
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path
    from uuid import UUID

from src.core.models.lineage import DocumentLineage
from src.core.storage.strategies.base import DataNotFoundError, StorageError
from src.core.storage.strategies.json_storage import JsonStorage

from .base import BaseRepository, DocumentExistsError, DocumentNotFoundError, Repository

logger = logging.getLogger(__name__)


class LineageRepository(BaseRepository[DocumentLineage], Repository[DocumentLineage]):
    """Repository implementation for document lineage."""

    def __init__(self, storage_path: Path) -> None:
        """Initialize lineage repository.

        Args:
            storage_path: Path to storage directory
        """
        self._storage = JsonStorage(storage_path, DocumentLineage)
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        """Ensure storage is initialized."""
        try:
            self._storage._ensure_storage_path()
        except StorageError:
            logger.exception("Failed to initialize lineage storage")
            raise

    def get(self, doc_id: UUID) -> DocumentLineage:
        """Get document lineage by ID.

        Args:
            doc_id: Document ID

        Returns:
            The document lineage

        Raises:
            DocumentNotFoundError: If lineage not found
        """
        try:
            return self._storage.load(str(doc_id))
        except DataNotFoundError as e:
            raise DocumentNotFoundError(f"Document lineage not found: {doc_id}") from e
        except StorageError:
            logger.exception("Failed to load lineage for document %s", doc_id)
            raise

    def create(self, lineage: DocumentLineage) -> None:
        """Create new document lineage.

        Args:
            lineage: Document lineage to create

        Raises:
            DocumentExistsError: If lineage already exists
        """
        if self.exists(lineage.doc_id):
            raise DocumentExistsError(f"Document lineage already exists: {lineage.doc_id}")

        try:
            self._storage.save(str(lineage.doc_id), lineage)
        except StorageError:
            logger.exception("Failed to create lineage for document %s", lineage.doc_id)
            raise

    def update(self, lineage: DocumentLineage) -> None:
        """Update existing document lineage.

        Args:
            lineage: Document lineage to update

        Raises:
            DocumentNotFoundError: If lineage not found
        """
        if not self.exists(lineage.doc_id):
            raise DocumentNotFoundError(f"Document lineage not found: {lineage.doc_id}")

        try:
            self._storage.save(str(lineage.doc_id), lineage)
        except StorageError:
            logger.exception("Failed to update lineage for document %s", lineage.doc_id)
            raise

    def delete(self, doc_id: UUID) -> None:
        """Delete document lineage.

        Args:
            doc_id: ID of document lineage to delete

        Raises:
            DocumentNotFoundError: If lineage not found
        """
        try:
            self._storage.delete(str(doc_id))
        except DataNotFoundError as e:
            raise DocumentNotFoundError(f"Document lineage not found: {doc_id}") from e
        except StorageError:
            logger.exception("Failed to delete lineage for document %s", doc_id)
            raise

    def exists(self, doc_id: UUID) -> bool:
        """Check if document lineage exists.

        Args:
            doc_id: Document ID to check

        Returns:
            True if lineage exists, False otherwise
        """
        return self._storage.exists(str(doc_id))

    def list_ids(self) -> set[UUID]:
        """Get all document lineage IDs.

        Returns:
            Set of document IDs with lineage
        """
        try:
            files = list(self._storage.storage_path.glob("*.json"))
            return {UUID(f.stem) for f in files if f.stem != "index" and UUID.is_valid_uuid(f.stem)}
        except Exception as e:
            logger.exception("Failed to list lineage IDs")
            raise StorageError(f"Failed to list lineage: {e}") from e

    def get_by_origin(self, origin_id: UUID) -> list[DocumentLineage]:
        """Get all lineage records with given origin.

        Args:
            origin_id: Origin document ID

        Returns:
            List of document lineage records
        """
        try:
            all_ids = self.list_ids()
            result = []
            for doc_id in all_ids:
                lineage = self.get(doc_id)
                if lineage.origin_id == origin_id:
                    result.append(lineage)
            return result
        except Exception as e:
            logger.exception("Failed to get lineage by origin %s", origin_id)
            raise StorageError(f"Failed to query lineage: {e}") from e

    def get_by_time_range(
        self, start_time: datetime | None = None, end_time: datetime | None = None
    ) -> list[DocumentLineage]:
        """Get all lineage records within time range.

        Args:
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)

        Returns:
            List of document lineage records
        """
        try:
            all_ids = self.list_ids()
            result = []
            for doc_id in all_ids:
                lineage = self.get(doc_id)
                if start_time and lineage.created_at < start_time:
                    continue
                if end_time and lineage.created_at > end_time:
                    continue
                result.append(lineage)
            return result
        except Exception as e:
            logger.exception("Failed to get lineage by time range")
            raise StorageError(f"Failed to query lineage: {e}") from e
