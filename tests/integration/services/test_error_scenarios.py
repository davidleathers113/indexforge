"""Integration tests for service error scenarios and recovery."""

import asyncio
from typing import Any, Dict, List

import pytest

from src.core.errors import (
    ServiceError,
    ServiceInitializationError,
    ServiceNotInitializedError,
    ServiceStateError,
)
from src.core.metrics import ServiceMetricsCollector
from src.core.settings import Settings
from src.services import RedisService, WeaviateClient
from src.services.factory import ServiceFactory


@pytest.fixture
async def settings() -> Settings:
    """Create test settings with invalid configurations."""
    return Settings(
        redis_url="redis://invalid-host:6379/0",
        redis_pool_size=5,
        weaviate_url="http://invalid-host:8080",
        weaviate_api_key="invalid-key",
    )


@pytest.fixture
async def metrics_collector() -> ServiceMetricsCollector:
    """Create metrics collector for testing."""
    return ServiceMetricsCollector(
        service_name="test-service",
        max_history=1000,
        memory_threshold_mb=500,
    )


class TestServiceErrorScenarios:
    """Test service error handling and recovery scenarios."""

    @pytest.mark.asyncio
    async def test_service_initialization_failure(self, settings: Settings):
        """Test handling of service initialization failures."""
        with pytest.raises(ServiceInitializationError) as exc_info:
            await ServiceFactory.create_cache_service(settings)
        assert "Failed to initialize Redis service" in str(exc_info.value)

        with pytest.raises(ServiceInitializationError) as exc_info:
            await ServiceFactory.create_vector_service(settings)
        assert "Failed to initialize Weaviate service" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_service_state_transitions(self, settings: Settings):
        """Test service state transitions during errors."""
        service = RedisService(settings)
        assert service.state == "created"

        with pytest.raises(ServiceInitializationError):
            await service.initialize()
        assert service.state == "error"

        # Test recovery attempt
        settings.redis_url = "redis://localhost:6379/0"  # Valid URL
        await service.initialize()
        assert service.state == "running"

    @pytest.mark.asyncio
    async def test_concurrent_error_handling(
        self, settings: Settings, metrics_collector: ServiceMetricsCollector
    ):
        """Test handling of errors during concurrent operations."""
        settings.redis_url = "redis://localhost:6379/0"  # Valid URL
        service = RedisService(settings)
        await service.initialize()

        # Simulate concurrent operations with some failures
        async def operation(key: str, should_fail: bool) -> None:
            if should_fail:
                with pytest.raises(ServiceError):
                    await service.set(key, "value", expire_in_seconds=-1)  # Invalid TTL
            else:
                await service.set(key, "value")

        operations = [operation(f"key_{i}", i % 2 == 0) for i in range(10)]  # Even keys will fail
        await asyncio.gather(*operations, return_exceptions=True)

        # Verify metrics
        metrics = service.get_metrics()
        assert metrics["error_count"] > 0
        assert metrics["success_count"] > 0

    @pytest.mark.asyncio
    async def test_error_recovery_mechanisms(self, settings: Settings):
        """Test service error recovery mechanisms."""
        settings.redis_url = "redis://localhost:6379/0"  # Valid URL
        service = RedisService(settings)
        await service.initialize()

        # Test automatic retry on temporary failures
        await service.set("test_key", "test_value")

        # Simulate network interruption by stopping Redis
        await service.cleanup()  # Force disconnect

        # Test recovery
        with pytest.raises(ServiceError):
            await service.get("test_key")

        # Reinitialize and verify recovery
        await service.initialize()
        value = await service.get("test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_resource_cleanup_after_errors(self, settings: Settings):
        """Test proper resource cleanup after errors."""
        settings.redis_url = "redis://localhost:6379/0"  # Valid URL
        service = RedisService(settings)
        await service.initialize()

        # Create some test data
        test_keys = [f"cleanup_test_{i}" for i in range(5)]
        for key in test_keys:
            await service.set(key, "test_value")

        # Simulate error condition
        await service.cleanup()

        # Verify cleanup
        service = RedisService(settings)
        await service.initialize()

        for key in test_keys:
            value = await service.get(key)
            assert value is None, f"Key {key} should have been cleaned up"

    @pytest.mark.asyncio
    async def test_metrics_during_errors(
        self, settings: Settings, metrics_collector: ServiceMetricsCollector
    ):
        """Test metrics collection during error scenarios."""
        settings.redis_url = "redis://localhost:6379/0"  # Valid URL
        service = RedisService(settings)
        service._metrics = metrics_collector
        await service.initialize()

        # Generate some errors
        error_keys = [f"error_key_{i}" for i in range(5)]
        for key in error_keys:
            try:
                await service.set(key, "value", expire_in_seconds=-1)  # Invalid TTL
            except ServiceError:
                pass

        # Verify error metrics
        metrics = service.get_metrics()
        assert metrics["error_count"] >= len(error_keys)
        assert "error_rate" in metrics
        assert metrics["error_rate"] > 0

        # Verify error tracking in metrics collector
        collector_metrics = metrics_collector.get_current_metrics()
        assert collector_metrics["error_operations"] >= len(error_keys)
        assert collector_metrics["total_operations"] >= len(error_keys)
