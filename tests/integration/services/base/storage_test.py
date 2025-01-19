"""Base classes for storage service integration tests.

This module provides the foundational test infrastructure for storage service tests,
including common verification methods and test utilities.
"""

from typing import Generic, TypeVar
from uuid import UUID

from src.core.models.base import BaseModel
from src.services.storage import BaseStorageService


T = TypeVar("T", bound=BaseModel)


class BaseStorageTest(Generic[T]):
    """Base class for storage service tests providing common test infrastructure."""

    @staticmethod
    async def verify_storage_operation(
        storage_service: BaseStorageService,
        test_data: T,
        stored_id: UUID | None = None,
    ) -> UUID:
        """Verify basic storage operations.

        Args:
            storage_service: Storage service to test
            test_data: Test data to store
            stored_id: Optional ID of already stored data

        Returns:
            UUID of stored data
        """
        # Store if not already stored
        if stored_id is None:
            stored_id = await storage_service.store(test_data)
            assert isinstance(stored_id, UUID)

        # Verify retrieval
        retrieved = await storage_service.get(stored_id)
        assert retrieved is not None
        assert retrieved == test_data

        return stored_id

    @staticmethod
    async def verify_batch_operations(
        storage_service: BaseStorageService,
        test_data: list[T],
    ) -> list[UUID]:
        """Verify batch storage operations.

        Args:
            storage_service: Storage service to test
            test_data: List of test data to store

        Returns:
            List of stored data IDs
        """
        # Store batch
        stored_ids = await storage_service.store_batch(test_data)
        assert len(stored_ids) == len(test_data)
        assert all(isinstance(id_, UUID) for id_ in stored_ids)

        # Verify batch retrieval
        retrieved = await storage_service.get_batch(stored_ids)
        assert len(retrieved) == len(test_data)
        assert all(r == d for r, d in zip(retrieved, test_data, strict=False))

        return stored_ids

    @staticmethod
    async def verify_metrics(storage_service: BaseStorageService) -> None:
        """Verify metrics collection.

        Args:
            storage_service: Storage service to test
        """
        metrics = storage_service.get_metrics()
        assert metrics.operations_count > 0
        assert metrics.successful_operations > 0
        assert metrics.failed_operations == 0
        assert metrics.total_processing_time > 0

    @staticmethod
    async def verify_health_check(storage_service: BaseStorageService) -> None:
        """Verify health check functionality.

        Args:
            storage_service: Storage service to test
        """
        health = await storage_service.health_check()
        assert health.is_healthy
        assert health.status == "ok"
        assert health.details is not None
        assert health.details.get("metrics") is not None
