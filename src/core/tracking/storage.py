"""Storage management for document tracking.

This module provides a type-safe implementation of document storage with proper
handling of document types, relationships, and metadata.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Protocol, TypeVar, cast
from uuid import UUID

from ..models.documents import Document, DocumentMetadata, DocumentStatus, DocumentType

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

    def delete_document(self, doc_id: UUID) -> None:
        """Delete a document."""
        ...


class BaseStorage(ABC):
    """Abstract base class for storage implementations."""

    def __init__(self, storage_path: Path) -> None:
        """Initialize storage.

        Args:
            storage_path: Path to storage directory
        """
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

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

    def __init__(self, storage_path: Path) -> None:
        """Initialize document storage.

        Args:
            storage_path: Path to storage directory
        """
        super().__init__(storage_path)
        self.documents: Dict[UUID, T] = {}
        self._load_data()

    def get_document(self, doc_id: UUID) -> Optional[T]:
        """Retrieve a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document if found, None otherwise
        """
        return self.documents.get(doc_id)

    def save_document(self, document: T) -> None:
        """Save a document.

        Args:
            document: Document to save
        """
        if not isinstance(document.metadata.doc_type, DocumentType):
            raise ValueError(f"Invalid document type: {document.metadata.doc_type}")

        self.documents[document.id] = document
        self._save_data()

    def delete_document(self, doc_id: UUID) -> None:
        """Delete a document.

        Args:
            doc_id: Document ID to delete

        Raises:
            KeyError: If document not found
        """
        if doc_id not in self.documents:
            raise KeyError(f"Document {doc_id} not found")

        del self.documents[doc_id]
        self._save_data()

    def _load_data(self) -> None:
        """Load documents from storage."""
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

    def _save_data(self) -> None:
        """Save documents to storage."""
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
