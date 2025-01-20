"""Document storage service implementation.

This module provides the implementation of document storage operations,
including metrics collection and error handling.
"""

from typing import TypeVar
from uuid import UUID, uuid4

from src.core.interfaces.metrics import MetricsProvider
from src.core.interfaces.storage import DocumentStorage
from src.core.models.documents import Document, DocumentMetadata, DocumentType
from src.core.settings import Settings
from src.core.types.storage import StorageMetrics

from .base import BaseStorageService, BatchConfig, BatchResult

T = TypeVar("T", bound=Document)


class DocumentStorageService(BaseStorageService, DocumentStorage[T]):
    """Implementation of document storage operations with metrics and batch support."""

    def __init__(
        self,
        settings: Settings,
        metrics: StorageMetrics | None = None,
        metrics_provider: MetricsProvider | None = None,
        batch_config: BatchConfig | None = None,
    ) -> None:
        """Initialize document storage.

        Args:
            settings: Application settings
            metrics: Optional storage metrics collector
            metrics_provider: Optional metrics provider for detailed metrics
            batch_config: Optional batch operation configuration
        """
        super().__init__(
            metrics=metrics, metrics_provider=metrics_provider, batch_config=batch_config
        )
        self._documents: dict[UUID, T] = {}
        self._settings = settings

    def store_document(self, document: T) -> UUID:
        """Store a document.

        Args:
            document: Document to store

        Returns:
            UUID: Generated document ID

        Raises:
            ValueError: If document is invalid
        """
        if not document:
            raise ValueError("Document cannot be None")

        self._time_operation("store_document")
        try:
            doc_id = uuid4()
            self._documents[doc_id] = document
            self._record_operation("store")
            return doc_id
        finally:
            self._stop_timing("store_document")

    def get_document(self, document_id: UUID) -> T:
        """Retrieve a document by ID.

        Args:
            document_id: ID of document to retrieve

        Returns:
            T: Retrieved document

        Raises:
            KeyError: If document does not exist
        """
        self._time_operation("get_document")
        try:
            if document_id not in self._documents:
                raise KeyError(f"Document {document_id} not found")

            document = self._documents[document_id]
            self._record_operation("get")
            return document
        finally:
            self._stop_timing("get_document")

    def update_document(self, document_id: UUID, document: T) -> None:
        """Update a document.

        Args:
            document_id: ID of document to update
            document: Updated document

        Raises:
            ValueError: If document is invalid
            KeyError: If document does not exist
        """
        if not document:
            raise ValueError("Document cannot be None")

        self._time_operation("update_document")
        try:
            if document_id not in self._documents:
                raise KeyError(f"Document {document_id} not found")

            self._documents[document_id] = document
            self._record_operation("update")
        finally:
            self._stop_timing("update_document")

    def delete_document(self, document_id: UUID) -> None:
        """Delete a document.

        Args:
            document_id: ID of document to delete

        Raises:
            KeyError: If document does not exist
        """
        self._time_operation("delete_document")
        try:
            if document_id not in self._documents:
                raise KeyError(f"Document {document_id} not found")

            del self._documents[document_id]
            self._record_operation("delete")
        finally:
            self._stop_timing("delete_document")

    def batch_store_documents(self, documents: list[T]) -> BatchResult[T]:
        """Store multiple documents in a batch operation.

        Args:
            documents: List of documents to store

        Returns:
            BatchResult containing successful and failed documents
        """
        return self.process_batch(documents, "store_document")

    def batch_update_documents(self, updates: list[tuple[UUID, T]]) -> BatchResult[tuple[UUID, T]]:
        """Update multiple documents in a batch operation.

        Args:
            updates: List of (document_id, document) pairs to update

        Returns:
            BatchResult containing successful and failed updates
        """
        return self.process_batch(updates, "update_document")

    def check_health(self) -> tuple[bool, str]:
        """Check the health of the document storage service.

        Returns:
            Tuple containing:
                - bool: True if service is healthy
                - str: Status message
        """
        try:
            # Perform basic health check
            metadata = DocumentMetadata(
                title="Health Check Document",
                doc_type=DocumentType.TEXT,
            )
            test_doc = Document(metadata=metadata)
            doc_id = self.store_document(test_doc)
            self.delete_document(doc_id)
            return True, "Document storage service is healthy"
        except Exception as e:
            return False, f"Document storage health check failed: {e!s}"
