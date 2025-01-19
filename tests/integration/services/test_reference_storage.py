"""Integration tests for reference storage service.

This module provides focused tests for reference storage operations,
including lifecycle, batch processing, and error handling.
"""

from collections.abc import AsyncGenerator
from uuid import UUID

import pytest
from pytest_asyncio import fixture
from tests.integration.services.base.storage_test import BaseStorageTest
from tests.integration.services.builders.test_data import ReferenceBuilder

from src.core.models.references import Reference
from src.core.settings import Settings
from src.services.storage import BatchConfig, ReferenceStorageService


@fixture
async def settings() -> Settings:
    """Create test settings."""
    return Settings(
        batch_size=100,
        max_retries=3,
        retry_delay=0.1,
    )


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


@fixture
async def test_reference() -> Reference:
    """Create a test reference."""
    return (
        ReferenceBuilder()
        .with_source(UUID(int=1))
        .with_target(UUID(int=2))
        .with_type("cites")
        .build()
    )


@fixture
async def test_references() -> list[Reference]:
    """Create a list of test references."""
    builder = ReferenceBuilder()
    return [
        builder.with_source(UUID(int=1))
        .with_target(UUID(int=i + 2))
        .with_type("cites")
        .with_confidence(0.8 + i * 0.05)
        .build()
        for i in range(5)
    ]


class TestReferenceStorage(BaseStorageTest[Reference]):
    """Test reference storage operations."""

    @pytest.mark.asyncio
    async def test_reference_lifecycle(
        self,
        reference_storage: ReferenceStorageService,
        test_reference: Reference,
    ):
        """Test basic reference lifecycle operations."""
        # Store and verify
        await reference_storage.store_reference(test_reference)
        refs = await reference_storage.get_references(test_reference.source_id)
        assert len(refs) == 1
        assert refs[0] == test_reference

        # Delete and verify
        await reference_storage.delete_reference(test_reference)
        refs = await reference_storage.get_references(test_reference.source_id)
        assert len(refs) == 0

    @pytest.mark.asyncio
    async def test_batch_operations(
        self,
        reference_storage: ReferenceStorageService,
        test_references: list[Reference],
    ):
        """Test batch reference operations."""
        # Store batch
        result = await reference_storage.batch_store_references(test_references)
        assert result.success_count == len(test_references)
        assert result.failure_count == 0

        # Verify storage
        refs = await reference_storage.get_references(test_references[0].source_id)
        assert len(refs) == len(test_references)
        assert all(ref in refs for ref in test_references)

        # Delete batch
        result = await reference_storage.batch_delete_references(test_references)
        assert result.success_count == len(test_references)
        assert result.failure_count == 0

        # Verify deletion
        refs = await reference_storage.get_references(test_references[0].source_id)
        assert len(refs) == 0

    @pytest.mark.asyncio
    async def test_error_handling(
        self,
        reference_storage: ReferenceStorageService,
        test_reference: Reference,
    ):
        """Test error handling scenarios."""
        # Test invalid reference retrieval
        invalid_id = UUID(int=0)
        refs = await reference_storage.get_references(invalid_id)
        assert len(refs) == 0

        # Test invalid reference deletion (should raise KeyError)
        with pytest.raises(KeyError):
            await reference_storage.delete_reference(test_reference)

    @pytest.mark.asyncio
    async def test_metrics_and_health(
        self,
        reference_storage: ReferenceStorageService,
        test_reference: Reference,
    ):
        """Test metrics collection and health checks."""
        # Perform operations
        await reference_storage.store_reference(test_reference)
        await reference_storage.get_references(test_reference.source_id)
        await reference_storage.delete_reference(test_reference)

        # Verify metrics
        await self.verify_metrics(reference_storage)

        # Verify health check
        await self.verify_health_check(reference_storage)

    @pytest.mark.asyncio
    async def test_bidirectional_references(
        self,
        reference_storage: ReferenceStorageService,
    ):
        """Test bidirectional reference relationships."""
        # Create bidirectional references
        ref1 = (
            ReferenceBuilder()
            .with_source(UUID(int=1))
            .with_target(UUID(int=2))
            .with_type("cites")
            .build()
        )
        ref2 = (
            ReferenceBuilder()
            .with_source(UUID(int=2))
            .with_target(UUID(int=1))
            .with_type("cited_by")
            .build()
        )

        # Store references
        await reference_storage.store_reference(ref1)
        await reference_storage.store_reference(ref2)

        # Verify forward references
        forward_refs = await reference_storage.get_references(ref1.source_id)
        assert len(forward_refs) == 1
        assert forward_refs[0] == ref1

        # Verify backward references
        back_refs = await reference_storage.get_references(ref2.source_id)
        assert len(back_refs) == 1
        assert back_refs[0] == ref2

        # Verify reference types
        assert forward_refs[0].reference_type == "cites"
        assert back_refs[0].reference_type == "cited_by"

    @pytest.mark.asyncio
    async def test_reference_confidence(
        self,
        reference_storage: ReferenceStorageService,
        test_references: list[Reference],
    ):
        """Test reference confidence handling."""
        # Store references with different confidence scores
        await reference_storage.batch_store_references(test_references)

        # Verify confidence values are preserved
        refs = await reference_storage.get_references(test_references[0].source_id)
        assert len(refs) == len(test_references)

        # Verify confidence ordering
        confidences = [ref.confidence for ref in refs]
        assert all(confidences[i] <= confidences[i + 1] for i in range(len(confidences) - 1))
