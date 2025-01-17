"""Integration tests for chunk storage service.

This module provides focused tests for chunk storage operations,
including lifecycle, batch processing, and error handling.
"""

from typing import AsyncGenerator
from uuid import UUID

import pytest
from pytest_asyncio import fixture

from src.core.models.chunks import Chunk
from src.core.settings import Settings
from src.services.storage import BatchConfig, ChunkStorageService
from tests.integration.services.base.storage_test import BaseStorageTest
from tests.integration.services.builders.test_data import ChunkBuilder


@fixture
async def settings() -> Settings:
    """Create test settings."""
    return Settings(
        batch_size=100,
        max_retries=3,
        retry_delay=0.1,
    )


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
async def test_chunk() -> Chunk:
    """Create a test chunk."""
    return ChunkBuilder().with_document_id(UUID(int=1)).build()


@fixture
async def test_chunks() -> list[Chunk]:
    """Create a list of test chunks."""
    builder = ChunkBuilder()
    return [
        builder.with_document_id(UUID(int=1))
        .with_indices(i * 10, (i + 1) * 10)
        .with_content(f"Chunk {i} content")
        .build()
        for i in range(5)
    ]


class TestChunkStorage(BaseStorageTest[Chunk]):
    """Test chunk storage operations."""

    @pytest.mark.asyncio
    async def test_chunk_lifecycle(
        self,
        chunk_storage: ChunkStorageService,
        test_chunk: Chunk,
    ):
        """Test basic chunk lifecycle operations."""
        # Store and verify
        chunk_id = await self.verify_storage_operation(chunk_storage, test_chunk)

        # Update
        updated_content = "Updated chunk content"
        test_chunk.content = updated_content
        await chunk_storage.update_chunk(chunk_id, test_chunk)

        # Verify update
        retrieved = await chunk_storage.get_chunk(chunk_id)
        assert retrieved is not None
        assert retrieved.content == updated_content

        # Delete and verify
        await chunk_storage.delete_chunk(chunk_id)
        deleted = await chunk_storage.get_chunk(chunk_id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_batch_operations(
        self,
        chunk_storage: ChunkStorageService,
        test_chunks: list[Chunk],
    ):
        """Test batch chunk operations."""
        # Store batch
        chunk_ids = await self.verify_batch_operations(chunk_storage, test_chunks)

        # Update batch
        updates = []
        for chunk_id, chunk in zip(chunk_ids, test_chunks):
            chunk.content = f"Updated {chunk.content}"
            updates.append((chunk_id, chunk))

        result = await chunk_storage.batch_update_chunks(updates)
        assert result.success_count == len(updates)
        assert result.failure_count == 0

        # Verify updates
        retrieved = await chunk_storage.get_chunks(chunk_ids)
        assert all(chunk.content.startswith("Updated") for chunk in retrieved if chunk)

        # Delete batch
        await chunk_storage.delete_chunks(chunk_ids)
        deleted = await chunk_storage.get_chunks(chunk_ids)
        assert all(chunk is None for chunk in deleted)

    @pytest.mark.asyncio
    async def test_error_handling(
        self,
        chunk_storage: ChunkStorageService,
        test_chunk: Chunk,
    ):
        """Test error handling scenarios."""
        # Test invalid chunk retrieval
        invalid_id = UUID(int=0)
        result = await chunk_storage.get_chunk(invalid_id)
        assert result is None

        # Test invalid chunk update
        with pytest.raises(Exception):
            await chunk_storage.update_chunk(invalid_id, test_chunk)

        # Test invalid chunk deletion (should not raise)
        await chunk_storage.delete_chunk(invalid_id)

    @pytest.mark.asyncio
    async def test_metrics_and_health(
        self,
        chunk_storage: ChunkStorageService,
        test_chunk: Chunk,
    ):
        """Test metrics collection and health checks."""
        # Perform operations
        chunk_id = await chunk_storage.store_chunk(test_chunk)
        await chunk_storage.get_chunk(chunk_id)
        await chunk_storage.delete_chunk(chunk_id)

        # Verify metrics
        await self.verify_metrics(chunk_storage)

        # Verify health check
        await self.verify_health_check(chunk_storage)

    @pytest.mark.asyncio
    async def test_document_chunk_relationship(
        self,
        chunk_storage: ChunkStorageService,
        test_chunks: list[Chunk],
    ):
        """Test chunks associated with the same document."""
        # Store chunks for same document
        chunk_ids = []
        for chunk in test_chunks:
            chunk_id = await chunk_storage.store_chunk(chunk)
            chunk_ids.append(chunk_id)

        # Verify all chunks have same document ID
        retrieved = await chunk_storage.get_chunks(chunk_ids)
        assert all(
            chunk.metadata.document_id == test_chunks[0].metadata.document_id
            for chunk in retrieved
            if chunk
        )

        # Verify chunk ordering by indices
        assert all(
            chunk.metadata.start_index < chunk.metadata.end_index for chunk in retrieved if chunk
        )
        assert all(
            retrieved[i].metadata.end_index <= retrieved[i + 1].metadata.start_index
            for i in range(len(retrieved) - 1)
            if retrieved[i] and retrieved[i + 1]
        )
