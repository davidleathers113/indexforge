"""Integration tests for storage service implementations.

This module provides comprehensive integration tests for document, chunk, and reference
storage services, including batch operations, metrics collection, and error scenarios.
"""

import asyncio
from collections.abc import AsyncGenerator
from uuid import UUID

import pytest
from pytest_asyncio import fixture

from src.core.models.chunks import Chunk, ChunkMetadata
from src.core.models.documents import Document, DocumentMetadata, DocumentType
from src.core.settings import Settings
from src.services.storage import (
    BatchConfig,
    ChunkStorageService,
    DocumentStorageService,
    ReferenceStorageService,
)


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
async def chunk_storage(settings: Settings) -> AsyncGenerator[ChunkStorageService, None]:
    """Create and initialize chunk storage service."""
    service = ChunkStorageService(
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
async def reference_storage(settings: Settings) -> AsyncGenerator[ReferenceStorageService, None]:
    """Create and initialize reference storage service."""
    service = ReferenceStorageService(
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


class TestStorageIntegration:
    """Test storage service integration scenarios."""

    @pytest.mark.asyncio
    async def test_document_lifecycle(self, document_storage: DocumentStorageService):
        """Test complete document lifecycle operations."""
        # Create test document
        metadata = DocumentMetadata(
            title="Test Document",
            source="test",
            doc_type=DocumentType.TEXT,
        )
        document = Document(
            content="Test content",
            metadata=metadata,
        )

        # Store document
        doc_id = await document_storage.store_document(document)
        assert isinstance(doc_id, UUID)

        # Retrieve document
        retrieved = await document_storage.get_document(doc_id)
        assert retrieved is not None
        assert retrieved.content == document.content
        assert retrieved.metadata.title == document.metadata.title

        # Update document
        updated_content = "Updated content"
        document.content = updated_content
        await document_storage.update_document(doc_id, document)

        # Verify update
        retrieved = await document_storage.get_document(doc_id)
        assert retrieved is not None
        assert retrieved.content == updated_content

        # Delete document
        await document_storage.delete_document(doc_id)

        # Verify deletion
        retrieved = await document_storage.get_document(doc_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_batch_operations(
        self,
        document_storage: DocumentStorageService,
        chunk_storage: ChunkStorageService,
    ):
        """Test batch operations across storage services."""
        # Create test documents
        documents = []
        chunks = []

        for i in range(15):  # Create more than batch_size
            doc_metadata = DocumentMetadata(
                title=f"Doc {i}",
                source="test",
                doc_type=DocumentType.TEXT,
            )
            document = Document(
                content=f"Content {i}",
                metadata=doc_metadata,
            )
            documents.append(document)

            chunk_metadata = ChunkMetadata(
                document_id=UUID(int=i),
                start_index=0,
                end_index=10,
            )
            chunk = Chunk(
                content=f"Chunk {i}",
                metadata=chunk_metadata,
            )
            chunks.append(chunk)

        # Test batch document storage
        doc_ids = await document_storage.store_documents(documents)
        assert len(doc_ids) == len(documents)

        # Test batch chunk storage
        chunk_ids = await chunk_storage.store_chunks(chunks)
        assert len(chunk_ids) == len(chunks)

        # Test batch retrieval
        retrieved_docs = await document_storage.get_documents(doc_ids)
        assert len(retrieved_docs) == len(documents)

        retrieved_chunks = await chunk_storage.get_chunks(chunk_ids)
        assert len(retrieved_chunks) == len(chunks)

        # Test batch deletion
        await document_storage.delete_documents(doc_ids)
        await chunk_storage.delete_chunks(chunk_ids)

        # Verify deletions
        remaining_docs = await document_storage.get_documents(doc_ids)
        assert all(doc is None for doc in remaining_docs)

        remaining_chunks = await chunk_storage.get_chunks(chunk_ids)
        assert all(chunk is None for chunk in remaining_chunks)

    @pytest.mark.asyncio
    async def test_metrics_collection(
        self,
        document_storage: DocumentStorageService,
        chunk_storage: ChunkStorageService,
        reference_storage: ReferenceStorageService,
    ):
        """Test metrics collection across storage services."""
        # Create test data
        doc_metadata = DocumentMetadata(
            title="Test Doc",
            source="test",
            doc_type=DocumentType.TEXT,
        )
        document = Document(
            content="Test content",
            metadata=doc_metadata,
        )

        # Perform operations and verify metrics
        doc_id = await document_storage.store_document(document)

        metrics = document_storage.get_metrics()
        assert metrics.operations_count > 0
        assert metrics.successful_operations > 0
        assert metrics.failed_operations == 0
        assert metrics.total_processing_time > 0

        # Test chunk metrics
        chunk_metadata = ChunkMetadata(
            document_id=doc_id,
            start_index=0,
            end_index=10,
        )
        chunk = Chunk(
            content="Test chunk",
            metadata=chunk_metadata,
        )

        await chunk_storage.store_chunk(chunk)

        chunk_metrics = chunk_storage.get_metrics()
        assert chunk_metrics.operations_count > 0
        assert chunk_metrics.successful_operations > 0
        assert chunk_metrics.failed_operations == 0

    @pytest.mark.asyncio
    async def test_error_handling(
        self,
        document_storage: DocumentStorageService,
    ):
        """Test error handling and recovery."""
        # Test invalid document retrieval
        invalid_id = UUID(int=0)
        result = await document_storage.get_document(invalid_id)
        assert result is None

        # Test invalid document update
        doc_metadata = DocumentMetadata(
            title="Test Doc",
            source="test",
            doc_type=DocumentType.TEXT,
        )
        document = Document(
            content="Test content",
            metadata=doc_metadata,
        )

        with pytest.raises(Exception):
            await document_storage.update_document(invalid_id, document)

        # Test invalid document deletion
        await document_storage.delete_document(invalid_id)  # Should not raise

    @pytest.mark.asyncio
    async def test_concurrent_operations(
        self,
        document_storage: DocumentStorageService,
    ):
        """Test concurrent storage operations."""
        # Create test documents
        documents = []
        for i in range(50):
            metadata = DocumentMetadata(
                title=f"Doc {i}",
                source="test",
                doc_type=DocumentType.TEXT,
            )
            document = Document(
                content=f"Content {i}",
                metadata=metadata,
            )
            documents.append(document)

        # Perform concurrent store operations
        async def store_document(doc: Document) -> UUID:
            return await document_storage.store_document(doc)

        tasks = [store_document(doc) for doc in documents]
        doc_ids = await asyncio.gather(*tasks)

        assert len(doc_ids) == len(documents)
        assert len(set(doc_ids)) == len(documents)  # All IDs should be unique

        # Perform concurrent retrievals
        async def get_document(doc_id: UUID) -> Document | None:
            return await document_storage.get_document(doc_id)

        tasks = [get_document(doc_id) for doc_id in doc_ids]
        retrieved_docs = await asyncio.gather(*tasks)

        assert len(retrieved_docs) == len(documents)
        assert all(doc is not None for doc in retrieved_docs)

    @pytest.mark.asyncio
    async def test_reference_operations(
        self,
        document_storage: DocumentStorageService,
        reference_storage: ReferenceStorageService,
    ):
        """Test reference storage operations and document linking."""
        # Create source document
        source_metadata = DocumentMetadata(
            title="Source Doc",
            source="test",
            doc_type=DocumentType.TEXT,
        )
        source_doc = Document(
            content="Source content",
            metadata=source_metadata,
        )
        source_id = await document_storage.store_document(source_doc)

        # Create target documents
        target_docs = []
        target_ids = []
        for i in range(3):
            metadata = DocumentMetadata(
                title=f"Target Doc {i}",
                source="test",
                doc_type=DocumentType.TEXT,
            )
            document = Document(
                content=f"Target content {i}",
                metadata=metadata,
            )
            target_docs.append(document)
            doc_id = await document_storage.store_document(document)
            target_ids.append(doc_id)

        # Create references
        for target_id in target_ids:
            await reference_storage.create_reference(
                source_id=source_id,
                target_id=target_id,
                reference_type="cites",
                confidence=0.95,
            )

        # Verify references
        refs = await reference_storage.get_references(source_id)
        assert len(refs) == len(target_ids)
        for ref in refs:
            assert ref.source_id == source_id
            assert ref.target_id in target_ids
            assert ref.reference_type == "cites"
            assert ref.confidence == 0.95

        # Test reverse reference lookup
        for target_id in target_ids:
            back_refs = await reference_storage.get_back_references(target_id)
            assert len(back_refs) == 1
            assert back_refs[0].source_id == source_id

        # Test reference deletion
        await reference_storage.delete_references(source_id)
        refs = await reference_storage.get_references(source_id)
        assert len(refs) == 0

    @pytest.mark.asyncio
    async def test_cross_service_operations(
        self,
        document_storage: DocumentStorageService,
        chunk_storage: ChunkStorageService,
        reference_storage: ReferenceStorageService,
    ):
        """Test operations involving multiple storage services."""
        # Create parent document
        doc_metadata = DocumentMetadata(
            title="Parent Doc",
            source="test",
            doc_type=DocumentType.TEXT,
        )
        parent_doc = Document(
            content="Parent content with multiple chunks",
            metadata=doc_metadata,
        )
        parent_id = await document_storage.store_document(parent_doc)

        # Create chunks for the document
        chunks = []
        for i in range(3):
            chunk_metadata = ChunkMetadata(
                document_id=parent_id,
                start_index=i * 10,
                end_index=(i + 1) * 10,
            )
            chunk = Chunk(
                content=f"Chunk {i} content",
                metadata=chunk_metadata,
            )
            chunks.append(chunk)

        # Store chunks
        chunk_ids = await chunk_storage.store_chunks(chunks)

        # Create related document
        related_metadata = DocumentMetadata(
            title="Related Doc",
            source="test",
            doc_type=DocumentType.TEXT,
        )
        related_doc = Document(
            content="Related content",
            metadata=related_metadata,
        )
        related_id = await document_storage.store_document(related_doc)

        # Create reference between documents
        await reference_storage.create_reference(
            source_id=parent_id,
            target_id=related_id,
            reference_type="related",
            confidence=0.85,
        )

        # Verify complete structure
        # 1. Check parent document
        parent = await document_storage.get_document(parent_id)
        assert parent is not None
        assert parent.content == parent_doc.content

        # 2. Check chunks
        doc_chunks = await chunk_storage.get_chunks(chunk_ids)
        assert len(doc_chunks) == len(chunks)
        for chunk, original in zip(doc_chunks, chunks, strict=False):
            assert chunk is not None
            assert chunk.content == original.content
            assert chunk.metadata.document_id == parent_id

        # 3. Check references
        refs = await reference_storage.get_references(parent_id)
        assert len(refs) == 1
        assert refs[0].target_id == related_id

        # Test cascading delete
        await document_storage.delete_document(parent_id)

        # Verify cleanup
        deleted_doc = await document_storage.get_document(parent_id)
        assert deleted_doc is None

        deleted_chunks = await chunk_storage.get_chunks(chunk_ids)
        assert all(chunk is None for chunk in deleted_chunks)

        deleted_refs = await reference_storage.get_references(parent_id)
        assert len(deleted_refs) == 0

    @pytest.mark.asyncio
    async def test_service_health_checks(
        self,
        document_storage: DocumentStorageService,
        chunk_storage: ChunkStorageService,
        reference_storage: ReferenceStorageService,
    ):
        """Test health check functionality across storage services."""
        # Test document storage health
        doc_health = await document_storage.health_check()
        assert doc_health.is_healthy
        assert doc_health.status == "ok"
        assert doc_health.details is not None

        # Test chunk storage health
        chunk_health = await chunk_storage.health_check()
        assert chunk_health.is_healthy
        assert chunk_health.status == "ok"
        assert chunk_health.details is not None

        # Test reference storage health
        ref_health = await reference_storage.health_check()
        assert ref_health.is_healthy
        assert ref_health.status == "ok"
        assert ref_health.details is not None

        # Verify metrics in health check
        assert doc_health.details.get("metrics") is not None
        assert chunk_health.details.get("metrics") is not None
        assert ref_health.details.get("metrics") is not None
