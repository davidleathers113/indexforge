"""Integration tests for cross-service interactions.

This module tests interactions between different storage services,
ensuring they work together correctly in complex scenarios.
"""

from typing import AsyncGenerator, List
from uuid import UUID

import pytest
from pytest_asyncio import fixture

from src.core.models.chunks import Chunk
from src.core.models.documents import Document
from src.core.models.references import Reference
from src.core.settings import Settings
from src.services.storage import (
    BatchConfig,
    ChunkStorageService,
    DocumentStorageService,
    ReferenceStorageService,
)
from tests.integration.services.builders.test_data import (
    ChunkBuilder,
    DocumentBuilder,
    ReferenceBuilder,
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
        batch_config=BatchConfig(batch_size=10, max_retries=2),
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
        batch_config=BatchConfig(batch_size=10, max_retries=2),
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
        batch_config=BatchConfig(batch_size=10, max_retries=2),
    )
    try:
        yield service
    finally:
        await service.cleanup()


class TestCrossServiceIntegration:
    """Test interactions between different storage services."""

    @pytest.mark.asyncio
    async def test_document_chunk_lifecycle(
        self,
        document_storage: DocumentStorageService,
        chunk_storage: ChunkStorageService,
    ):
        """Test document and chunk lifecycle integration."""
        # Create and store document
        document = DocumentBuilder().build()
        doc_id = await document_storage.store_document(document)

        # Create and store chunks for document
        chunks = []
        chunk_ids = []
        for i in range(3):
            chunk = (
                ChunkBuilder()
                .with_document_id(doc_id)
                .with_indices(i * 10, (i + 1) * 10)
                .with_content(f"Chunk {i}")
                .build()
            )
            chunks.append(chunk)
            chunk_id = await chunk_storage.store_chunk(chunk)
            chunk_ids.append(chunk_id)

        # Verify document and chunks
        retrieved_doc = await document_storage.get_document(doc_id)
        assert retrieved_doc is not None
        assert retrieved_doc == document

        retrieved_chunks = await chunk_storage.get_chunks(chunk_ids)
        assert len(retrieved_chunks) == len(chunks)
        assert all(chunk is not None for chunk in retrieved_chunks)

        # Delete document and verify cascade to chunks
        await document_storage.delete_document(doc_id)
        deleted_doc = await document_storage.get_document(doc_id)
        assert deleted_doc is None

        deleted_chunks = await chunk_storage.get_chunks(chunk_ids)
        assert all(chunk is None for chunk in deleted_chunks)

    @pytest.mark.asyncio
    async def test_document_reference_graph(
        self,
        document_storage: DocumentStorageService,
        reference_storage: ReferenceStorageService,
    ):
        """Test document reference graph creation and traversal."""
        # Create documents
        docs: List[Document] = []
        doc_ids: List[UUID] = []
        for i in range(5):
            doc = DocumentBuilder().with_title(f"Doc {i}").with_content(f"Content {i}").build()
            docs.append(doc)
            doc_id = await document_storage.store_document(doc)
            doc_ids.append(doc_id)

        # Create reference graph
        # Doc 0 -> Doc 1 -> Doc 2
        #   |              ^
        #   v              |
        # Doc 3 -> Doc 4 ---
        references = [
            ReferenceBuilder()
            .with_source(doc_ids[0])
            .with_target(doc_ids[1])
            .with_type("cites")
            .build(),
            ReferenceBuilder()
            .with_source(doc_ids[0])
            .with_target(doc_ids[3])
            .with_type("cites")
            .build(),
            ReferenceBuilder()
            .with_source(doc_ids[1])
            .with_target(doc_ids[2])
            .with_type("cites")
            .build(),
            ReferenceBuilder()
            .with_source(doc_ids[3])
            .with_target(doc_ids[4])
            .with_type("cites")
            .build(),
            ReferenceBuilder()
            .with_source(doc_ids[4])
            .with_target(doc_ids[2])
            .with_type("cites")
            .build(),
        ]

        # Store references
        for ref in references:
            await reference_storage.store_reference(ref)

        # Verify forward references
        refs = await reference_storage.get_references(doc_ids[0])
        assert len(refs) == 2  # Doc 0 cites Doc 1 and Doc 3

        # Verify back references
        back_refs = await reference_storage.get_references(doc_ids[2])
        assert len(back_refs) == 2  # Doc 2 is cited by Doc 1 and Doc 4

        # Delete a document and verify reference cleanup
        await document_storage.delete_document(doc_ids[1])
        refs = await reference_storage.get_references(doc_ids[0])
        assert len(refs) == 1  # Only Doc 3 reference remains

    @pytest.mark.asyncio
    async def test_full_document_processing(
        self,
        document_storage: DocumentStorageService,
        chunk_storage: ChunkStorageService,
        reference_storage: ReferenceStorageService,
    ):
        """Test complete document processing workflow."""
        # Create and store source document
        source_doc = DocumentBuilder().with_title("Source").build()
        source_id = await document_storage.store_document(source_doc)

        # Create and store target documents
        target_docs = []
        target_ids = []
        for i in range(3):
            doc = (
                DocumentBuilder()
                .with_title(f"Target {i}")
                .with_content(f"Target content {i}")
                .build()
            )
            target_docs.append(doc)
            doc_id = await document_storage.store_document(doc)
            target_ids.append(doc_id)

        # Create chunks for source document
        source_chunks = []
        for i in range(3):
            chunk = (
                ChunkBuilder()
                .with_document_id(source_id)
                .with_indices(i * 10, (i + 1) * 10)
                .with_content(f"Source chunk {i}")
                .build()
            )
            source_chunks.append(chunk)
            await chunk_storage.store_chunk(chunk)

        # Create references from source to targets
        for i, target_id in enumerate(target_ids):
            ref = (
                ReferenceBuilder()
                .with_source(source_id)
                .with_target(target_id)
                .with_type("cites")
                .with_confidence(0.8 + i * 0.1)
                .build()
            )
            await reference_storage.store_reference(ref)

        # Verify complete structure
        # 1. Check source document
        retrieved_source = await document_storage.get_document(source_id)
        assert retrieved_source is not None
        assert retrieved_source == source_doc

        # 2. Check source chunks
        source_chunk_ids = [await chunk_storage.store_chunk(chunk) for chunk in source_chunks]
        retrieved_chunks = await chunk_storage.get_chunks(source_chunk_ids)
        assert len(retrieved_chunks) == len(source_chunks)
        assert all(chunk is not None for chunk in retrieved_chunks)

        # 3. Check references
        refs = await reference_storage.get_references(source_id)
        assert len(refs) == len(target_ids)
        assert all(ref.target_id in target_ids for ref in refs)

        # Test cascading delete
        await document_storage.delete_document(source_id)

        # Verify cleanup
        assert await document_storage.get_document(source_id) is None
        deleted_chunks = await chunk_storage.get_chunks(source_chunk_ids)
        assert all(chunk is None for chunk in deleted_chunks)
        deleted_refs = await reference_storage.get_references(source_id)
        assert len(deleted_refs) == 0
