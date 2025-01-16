"""Document storage service implementation."""

from typing import Dict, Optional, TypeVar
from uuid import UUID, uuid4

from src.core.errors import ServiceStateError
from src.core.interfaces.storage import DocumentStorage
from src.core.models.documents import Document
from src.services.base import BaseService
from src.services.storage.metrics import StorageMetricsService

T = TypeVar("T", bound=Document)


class DocumentStorageService(DocumentStorage, BaseService):
    """Implementation of document storage operations."""

    def __init__(self, metrics: StorageMetricsService) -> None:
        """Initialize document storage.

        Args:
            metrics: Storage metrics service
        """
        BaseService.__init__(self)
        self._documents: Dict[UUID, T] = {}
        self._metrics = metrics
        self._initialized = True

    def store_document(self, document: T) -> UUID:
        """Store a document.

        Args:
            document: Document to store

        Returns:
            UUID: Generated document ID

        Raises:
            ServiceStateError: If storage is not initialized
            ValueError: If document is invalid
        """
        if not self.is_initialized:
            raise ServiceStateError("Document storage is not initialized")

        if not document:
            raise ValueError("Document cannot be None")

        doc_id = uuid4()
        self._documents[doc_id] = document
        self._metrics.increment_storage_stat("document_count")
        self._metrics.increment_storage_stat("total_bytes", len(str(document).encode()))
        self._metrics.increment_operation_count("writes")
        return doc_id

    def get_document(self, doc_id: UUID) -> Optional[T]:
        """Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Optional[T]: Document if found, None otherwise

        Raises:
            ServiceStateError: If storage is not initialized
        """
        if not self.is_initialized:
            raise ServiceStateError("Document storage is not initialized")

        self._metrics.increment_operation_count("reads")
        return self._documents.get(doc_id)

    def update_document(self, doc_id: UUID, document: T) -> None:
        """Update a document.

        Args:
            doc_id: Document ID
            document: Updated document

        Raises:
            ServiceStateError: If storage is not initialized
            ValueError: If document is invalid
            KeyError: If document does not exist
        """
        if not self.is_initialized:
            raise ServiceStateError("Document storage is not initialized")

        if not document:
            raise ValueError("Document cannot be None")

        if doc_id not in self._documents:
            raise KeyError(f"Document with ID {doc_id} does not exist")

        old_size = len(str(self._documents[doc_id]).encode())
        new_size = len(str(document).encode())
        size_diff = new_size - old_size

        self._documents[doc_id] = document
        self._metrics.increment_storage_stat("total_bytes", size_diff)
        self._metrics.increment_operation_count("updates")

    def delete_document(self, doc_id: UUID) -> None:
        """Delete a document.

        Args:
            doc_id: Document ID

        Raises:
            ServiceStateError: If storage is not initialized
            KeyError: If document does not exist
        """
        if not self.is_initialized:
            raise ServiceStateError("Document storage is not initialized")

        if doc_id not in self._documents:
            raise KeyError(f"Document with ID {doc_id} does not exist")

        doc_size = len(str(self._documents[doc_id]).encode())
        del self._documents[doc_id]
        self._metrics.decrement_storage_stat("document_count")
        self._metrics.decrement_storage_stat("total_bytes", doc_size)
        self._metrics.increment_operation_count("deletes")
