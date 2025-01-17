"""Storage management for document tracking.

This module provides a type-safe implementation of document storage with proper
handling of document types, relationships, and metadata.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Optional, Protocol, TypeVar, cast
from uuid import UUID

from ..models.documents import Document, DocumentMetadata, DocumentStatus, DocumentType
from ..models.settings import Settings
from .metrics import StorageMetricsCollector

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Document)


class StorageProtocol(Protocol[T]):
    """Protocol defining the interface for document storage."""

    def get_document(self, doc_id: UUID) -> Optional[T]:
        """Retrieve a document by ID."""
        ...

    def save_document(self, document: T) -> None:
        """Save a document."""
        ...

    def update_document(self, doc_id: UUID, updates: Dict[str, Any]) -> None:
        """Update an existing document.

        Args:
            doc_id: ID of document to update
            updates: Dictionary of updates to apply

        Raises:
            KeyError: If document not found
            ValueError: If updates would create invalid document state
        """
        ...

    def delete_document(self, doc_id: UUID) -> None:
        """Delete a document."""
        ...


class BaseStorage(ABC):
    """Abstract base class for storage implementations."""

    def __init__(self, storage_path: Path, settings: Optional[Settings] = None) -> None:
        """Initialize storage.

        Args:
            storage_path: Path to storage directory
            settings: Optional settings for storage configuration
        """
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.settings = settings or Settings(storage_path=storage_path)
        self.metrics = (
            StorageMetricsCollector(self.settings) if self.settings.metrics_enabled else None
        )

    @abstractmethod
    def _load_data(self) -> None:
        """Load data from storage."""
        pass

    @abstractmethod
    def _save_data(self) -> None:
        """Save data to storage."""
        pass


class DocumentStorage(BaseStorage, StorageProtocol[T]):
    """Implementation of document storage with type safety."""

    def __init__(self, storage_path: Path, settings: Optional[Settings] = None) -> None:
        """Initialize document storage.

        Args:
            storage_path: Path to storage directory
            settings: Optional settings for storage configuration
        """
        super().__init__(storage_path, settings)
        self.documents: Dict[UUID, T] = {}
        self._load_data()

    def get_document(self, doc_id: UUID) -> Optional[T]:
        """Retrieve a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document if found, None otherwise
        """
        if self.metrics:
            self.metrics.start_operation("get_document")
        try:
            return self.documents.get(doc_id)
        finally:
            if self.metrics:
                self.metrics.end_operation("get_document")

    def save_document(self, document: T) -> None:
        """Save a document.

        Args:
            document: Document to save

        Raises:
            ValueError: If document type is invalid
        """
        if self.metrics:
            self.metrics.start_operation("save_document")
        try:
            if not isinstance(document.metadata.doc_type, DocumentType):
                raise ValueError(f"Invalid document type: {document.metadata.doc_type}")

            self.documents[document.id] = document
            self._save_data()
        finally:
            if self.metrics:
                self.metrics.end_operation("save_document")

    def update_document(self, doc_id: UUID, updates: Dict[str, Any]) -> None:
        """Update an existing document.

        Args:
            doc_id: ID of document to update
            updates: Dictionary of updates to apply

        Raises:
            KeyError: If document not found
            ValueError: If updates would create invalid document state
        """
        if self.metrics:
            self.metrics.start_operation("update_document")
        try:
            document = self.documents.get(doc_id)
            if not document:
                raise KeyError(f"Document {doc_id} not found")

            # Handle metadata updates
            if "metadata" in updates:
                metadata_updates = updates["metadata"]
                if "doc_type" in metadata_updates:
                    if not isinstance(metadata_updates["doc_type"], DocumentType):
                        raise ValueError(f"Invalid document type: {metadata_updates['doc_type']}")

                # Update metadata fields
                for key, value in metadata_updates.items():
                    setattr(document.metadata, key, value)

                # Always update the updated_at timestamp
                document.metadata.updated_at = datetime.now(UTC)

            # Handle status update
            if "status" in updates:
                if not isinstance(updates["status"], DocumentStatus):
                    raise ValueError(f"Invalid status: {updates['status']}")
                document.status = updates["status"]

            # Handle relationship updates
            if "parent_id" in updates:
                new_parent_id = updates["parent_id"]
                if new_parent_id is not None:
                    # Verify parent exists
                    parent = self.documents.get(new_parent_id)
                    if not parent:
                        raise ValueError(f"Parent document {new_parent_id} not found")

                    # Update parent's children
                    if doc_id not in parent.child_ids:
                        parent.child_ids.add(doc_id)
                        parent.metadata.updated_at = datetime.now(UTC)

                # Update document's parent
                document.parent_id = new_parent_id

            if "child_ids" in updates:
                new_child_ids = updates["child_ids"]
                # Verify all children exist
                for child_id in new_child_ids:
                    if child_id not in self.documents:
                        raise ValueError(f"Child document {child_id} not found")

                # Update document's children
                document.child_ids = set(new_child_ids)

            # Handle error message update
            if "error_message" in updates:
                document.error_message = updates["error_message"]

            self._save_data()
            logger.debug("Successfully updated document %s", doc_id)

        except (KeyError, ValueError) as e:
            logger.error("Failed to update document %s: %s", doc_id, str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error updating document %s: %s", doc_id, str(e))
            raise
        finally:
            if self.metrics:
                self.metrics.end_operation("update_document")

    def delete_document(self, doc_id: UUID) -> None:
        """Delete a document.

        Args:
            doc_id: Document ID to delete

        Raises:
            KeyError: If document not found
        """
        if self.metrics:
            self.metrics.start_operation("delete_document")
        try:
            if doc_id not in self.documents:
                raise KeyError(f"Document {doc_id} not found")

            del self.documents[doc_id]
            self._save_data()
        finally:
            if self.metrics:
                self.metrics.end_operation("delete_document")

    def _load_data(self) -> None:
        """Load documents from storage."""
        if self.metrics:
            self.metrics.start_operation("load_data")
        try:
            data_file = self.storage_path / "documents.json"
            if data_file.exists():
                data = json.loads(data_file.read_text())
                for doc_data in data.values():
                    metadata = DocumentMetadata(
                        title=doc_data["metadata"]["title"],
                        doc_type=DocumentType(doc_data["metadata"]["doc_type"]),
                        created_at=datetime.fromisoformat(doc_data["metadata"]["created_at"]),
                        updated_at=datetime.fromisoformat(doc_data["metadata"]["updated_at"]),
                        source_path=doc_data["metadata"].get("source_path"),
                        mime_type=doc_data["metadata"].get("mime_type"),
                        encoding=doc_data["metadata"].get("encoding"),
                        language=doc_data["metadata"].get("language"),
                        custom_metadata=doc_data["metadata"].get("custom_metadata", {}),
                    )
                    document = Document(
                        metadata=metadata,
                        id=UUID(doc_data["id"]),
                        status=DocumentStatus(doc_data["status"]),
                        parent_id=(
                            UUID(doc_data["parent_id"]) if doc_data.get("parent_id") else None
                        ),
                        child_ids={UUID(child_id) for child_id in doc_data.get("child_ids", [])},
                        error_message=doc_data.get("error_message"),
                    )
                    self.documents[document.id] = cast(T, document)
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            self.documents = {}
        finally:
            if self.metrics:
                self.metrics.end_operation("load_data")

    def _save_data(self) -> None:
        """Save documents to storage."""
        if self.metrics:
            self.metrics.start_operation("save_data")
        try:
            data = {}
            for doc_id, document in self.documents.items():
                data[str(doc_id)] = {
                    "id": str(document.id),
                    "metadata": {
                        "title": document.metadata.title,
                        "doc_type": document.metadata.doc_type.value,
                        "created_at": document.metadata.created_at.isoformat(),
                        "updated_at": document.metadata.updated_at.isoformat(),
                        "source_path": document.metadata.source_path,
                        "mime_type": document.metadata.mime_type,
                        "encoding": document.metadata.encoding,
                        "language": document.metadata.language,
                        "custom_metadata": document.metadata.custom_metadata,
                    },
                    "status": document.status.value,
                    "parent_id": str(document.parent_id) if document.parent_id else None,
                    "child_ids": [str(child_id) for child_id in document.child_ids],
                    "error_message": document.error_message,
                }
            data_file = self.storage_path / "documents.json"
            data_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Error saving documents: {e}")
            raise
        finally:
            if self.metrics:
                self.metrics.end_operation("save_data")
