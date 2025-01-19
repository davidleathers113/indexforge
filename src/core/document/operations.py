"""Document operations service.

This module provides document lifecycle management functionality through a service interface.
"""

from uuid import UUID, uuid4

from src.core.base import BaseService, ServiceState, ServiceStateError
from src.core.models import Document, DocumentMetadata, DocumentStatus, DocumentType, ProcessingStep
from src.core.models.document_operations import DocumentOperationMetadata, OperationMetadata
from src.core.storage.strategies.json_storage import JsonStorageStrategy


class DocumentOperationError(Exception):
    """Base exception for document operations."""


class DocumentNotFoundError(DocumentOperationError):
    """Exception raised when a document is not found."""


class DocumentOperationsService(BaseService):
    """Document operations service.

    Provides:
    - Document lifecycle management
    - CRUD operations
    - State tracking
    - Relationship management
    """

    def __init__(self, storage: JsonStorageStrategy):
        """Initialize document operations service.

        Args:
            storage: Storage strategy for document persistence.
        """
        super().__init__()
        self.storage = storage
        self.add_metadata("service_type", "document_operations")

    async def initialize(self) -> None:
        """Initialize the service.

        Verifies storage connection and prepares service state.

        Raises:
            ServiceStateError: If initialization fails
        """
        await super().initialize()
        try:
            # Verify storage connection
            await self.storage.health_check()
        except Exception as e:
            self._transition_state(ServiceState.ERROR)
            raise ServiceStateError(f"Failed to initialize storage: {e}") from e

    async def cleanup(self) -> None:
        """Clean up service resources."""
        await super().cleanup()
        # Storage cleanup handled by context manager

    async def create_document(
        self,
        content: str,
        metadata: DocumentMetadata | None = None,
        doc_type: DocumentType = DocumentType.TEXT,
    ) -> Document:
        """Create a new document.

        Args:
            content: Document content.
            metadata: Optional document metadata.
            doc_type: Document type.

        Returns:
            The created document.

        Raises:
            ServiceStateError: If service is not running
        """
        self._check_running()

        # Create operation metadata
        operation = OperationMetadata(
            type="create",
            author=metadata.author if metadata else "",
            status=DocumentStatus.PROCESSED,
        )

        # Create document metadata with operation tracking
        base_metadata = (
            metadata.dict()
            if metadata
            else {
                "title": "",
                "size_bytes": len(content.encode()),
                "custom_metadata": {},
            }
        )
        doc_metadata = DocumentOperationMetadata(
            **base_metadata,
            operation_history=[operation],
        )

        # Create document
        doc = Document(
            id=uuid4(),
            type=doc_type,
            status=DocumentStatus.PROCESSED,
            metadata=doc_metadata,
            content=content,
            processing_history=[ProcessingStep.EXTRACTION],
            error_message=None,
        )
        await self.storage.save(str(doc.id), doc.dict())
        return doc

    async def get_document(self, doc_id: UUID) -> Document:
        """Get a document by ID.

        Args:
            doc_id: Document ID.

        Returns:
            The requested document.

        Raises:
            DocumentNotFoundError: If document is not found
            ServiceStateError: If service is not running
        """
        self._check_running()
        data = await self.storage.load(str(doc_id))
        if not data:
            raise DocumentNotFoundError(f"Document {doc_id} not found")
        return Document.parse_obj(data)

    async def update_document(
        self,
        doc_id: UUID,
        content: str | None = None,
        metadata: dict | None = None,
    ) -> Document:
        """Update a document.

        Args:
            doc_id: Document ID.
            content: Optional new content.
            metadata: Optional metadata updates.

        Returns:
            The updated document.

        Raises:
            DocumentNotFoundError: If document is not found
            ServiceStateError: If service is not running
        """
        self._check_running()
        doc = await self.get_document(doc_id)

        if content is not None:
            doc.content = content

        if metadata:
            current_metadata = doc.metadata.dict()
            operation = OperationMetadata(
                type="update",
                author=metadata.get("author", current_metadata.get("author", "")),
                status=DocumentStatus.PROCESSED,
            )

            if isinstance(doc.metadata, DocumentOperationMetadata):
                doc.metadata.operation_history.append(operation)
                for key, value in metadata.items():
                    if hasattr(doc.metadata, key):
                        setattr(doc.metadata, key, value)
            else:
                # Convert to operation metadata if not already
                new_metadata = DocumentOperationMetadata(
                    **current_metadata,
                    operation_history=[operation],
                )
                for key, value in metadata.items():
                    if hasattr(new_metadata, key):
                        setattr(new_metadata, key, value)
                doc.metadata = new_metadata

        await self.storage.save(str(doc_id), doc.dict())
        return doc

    async def delete_document(self, doc_id: UUID) -> None:
        """Delete a document.

        Args:
            doc_id: Document ID.

        Raises:
            DocumentNotFoundError: If document is not found
            ServiceStateError: If service is not running
        """
        self._check_running()
        doc = await self.get_document(doc_id)
        doc.status = DocumentStatus.FAILED

        # Update operation history
        operation = OperationMetadata(
            type="delete",
            status=DocumentStatus.FAILED,
        )

        if isinstance(doc.metadata, DocumentOperationMetadata):
            doc.metadata.operation_history.append(operation)
        else:
            # Convert to operation metadata if not already
            doc.metadata = DocumentOperationMetadata(
                **doc.metadata.dict(),
                operation_history=[operation],
            )

        await self.storage.save(str(doc_id), doc.dict())

    async def list_documents(
        self, parent_id: UUID | None = None, active_only: bool = True
    ) -> list[Document]:
        """List documents.

        Args:
            parent_id: Optional parent document ID to filter by.
            active_only: Whether to return only active documents.

        Returns:
            List of matching documents.

        Raises:
            ServiceStateError: If service is not running
        """
        self._check_running()
        all_docs = []
        async for key, data in self.storage.iterate():
            doc = Document.parse_obj(data)
            if active_only and doc.status == DocumentStatus.FAILED:
                continue
            if parent_id is not None and getattr(doc.metadata, "parent_id", None) != parent_id:
                continue
            all_docs.append(doc)
        return sorted(all_docs, key=lambda d: d.metadata.created_at)

    async def health_check(self) -> bool:
        """Check service health.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            self._check_running()
            await self.storage.health_check()
            return True
        except Exception:
            return False
