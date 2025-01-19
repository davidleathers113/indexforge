"""Integration tests for document storage service.

This module provides focused tests for document storage operations,
including lifecycle, batch processing, and error handling.
"""

from collections.abc import AsyncGenerator
from uuid import UUID

import pytest
from pytest_asyncio import fixture
from tests.integration.services.base.storage_test import BaseStorageTest
from tests.integration.services.builders.test_data import DocumentBuilder

from src.core.models.documents import Document
from src.core.settings import Settings
from src.services.storage import BatchConfig, DocumentStorageService


@fixture
async def settings() -> Settings:
    """Create test settings."""
    return Settings(
        batch_size=100,
        max_retries=3,
        retry_delay=0.1,
    )


@fixture
async def document_storage(settings: Settings) -> AsyncGenerator[DocumentStorageService, None]:
    """Create and initialize document storage service."""
    service = DocumentStorageService(
        settings=settings,
        batch_config=BatchConfig(
            batch_size=10,
            max_retries=2,
        ),
    )
    try:
        yield service
    finally:
        await service.cleanup()


@fixture
async def test_document() -> Document:
    """Create a test document."""
    return DocumentBuilder().build()


@fixture
async def test_documents() -> list[Document]:
    """Create a list of test documents."""
    builder = DocumentBuilder()
    return [builder.with_title(f"Doc {i}").with_content(f"Content {i}").build() for i in range(5)]


class TestDocumentStorage(BaseStorageTest[Document]):
    """Test document storage operations."""

    @pytest.mark.asyncio
    async def test_document_lifecycle(
        self,
        document_storage: DocumentStorageService,
        test_document: Document,
    ):
        """Test basic document lifecycle operations."""
        # Store and verify
        doc_id = await self.verify_storage_operation(document_storage, test_document)

        # Update
        updated_content = "Updated content"
        test_document.content = updated_content
        await document_storage.update_document(doc_id, test_document)

        # Verify update
        retrieved = await document_storage.get_document(doc_id)
        assert retrieved is not None
        assert retrieved.content == updated_content

        # Delete and verify
        await document_storage.delete_document(doc_id)
        deleted = await document_storage.get_document(doc_id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_batch_operations(
        self,
        document_storage: DocumentStorageService,
        test_documents: list[Document],
    ):
        """Test batch document operations."""
        # Store batch
        doc_ids = await self.verify_batch_operations(document_storage, test_documents)

        # Update batch
        updates = []
        for doc_id, doc in zip(doc_ids, test_documents, strict=False):
            doc.content = f"Updated {doc.content}"
            updates.append((doc_id, doc))

        result = await document_storage.batch_update_documents(updates)
        assert result.success_count == len(updates)
        assert result.failure_count == 0

        # Verify updates
        retrieved = await document_storage.get_documents(doc_ids)
        assert all(doc.content.startswith("Updated") for doc in retrieved if doc)

        # Delete batch
        await document_storage.delete_documents(doc_ids)
        deleted = await document_storage.get_documents(doc_ids)
        assert all(doc is None for doc in deleted)

    @pytest.mark.asyncio
    async def test_error_handling(
        self,
        document_storage: DocumentStorageService,
        test_document: Document,
    ):
        """Test error handling scenarios."""
        # Test invalid document retrieval
        invalid_id = UUID(int=0)
        result = await document_storage.get_document(invalid_id)
        assert result is None

        # Test invalid document update
        with pytest.raises(Exception):
            await document_storage.update_document(invalid_id, test_document)

        # Test invalid document deletion (should not raise)
        await document_storage.delete_document(invalid_id)

    @pytest.mark.asyncio
    async def test_metrics_and_health(
        self,
        document_storage: DocumentStorageService,
        test_document: Document,
    ):
        """Test metrics collection and health checks."""
        # Perform operations
        doc_id = await document_storage.store_document(test_document)
        await document_storage.get_document(doc_id)
        await document_storage.delete_document(doc_id)

        # Verify metrics
        await self.verify_metrics(document_storage)

        # Verify health check
        await self.verify_health_check(document_storage)
