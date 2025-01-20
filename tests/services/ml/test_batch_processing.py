"""Tests for batch processing functionality.

This module tests batch processing operations, focusing on:
1. Basic batch operations
2. Resource-aware batch processing
3. Error handling in batch contexts
4. Concurrent batch operations
5. Batch size optimization
"""

import asyncio
from typing import List
from unittest.mock import Mock, patch

import pytest
from pydantic import BaseModel

from src.core.settings import Settings
from src.services.ml.errors import ResourceError, ValidationError
from src.services.ml.implementations.embedding import EmbeddingService
from src.services.ml.implementations.factories import ServiceFactory
from src.services.ml.monitoring.instrumentation import (
    InstrumentationConfig,
    PerformanceInstrumentor,
)
from src.services.ml.monitoring.metrics import MetricsCollector
from src.services.ml.optimization.resources import ResourceManager


class BatchTestData(BaseModel):
    """Test data model for batch operations."""

    text: str
    metadata: dict
    expected_size: int = 0


@pytest.fixture
def settings():
    """Create test settings with batch configuration."""
    return Settings(
        max_memory_mb=1000,
        batch_size=10,
        min_batch_size=2,
        max_batch_size=50,
        device="cpu",
        model_path="test_model",
    )


@pytest.fixture
def metrics_collector():
    """Create metrics collector."""
    return MetricsCollector()


@pytest.fixture
def resource_manager(settings):
    """Create resource manager."""
    return ResourceManager(settings)


@pytest.fixture
def instrumentor(metrics_collector, resource_manager):
    """Create performance instrumentor."""
    config = InstrumentationConfig(
        collect_profiles=True,
        track_resources=True,
    )
    return PerformanceInstrumentor(metrics_collector, resource_manager, config)


@pytest.fixture
async def service(settings, instrumentor):
    """Create service for batch testing."""
    service = await ServiceFactory.create_embedding_service(settings)
    service.set_instrumentor(instrumentor)
    return service


class TestBatchProcessing:
    """Tests for batch processing operations."""

    async def test_basic_batch_operation(self, service: EmbeddingService):
        """Test basic batch processing functionality."""
        # Create test batch
        batch = [BatchTestData(text=f"test{i}", metadata={"index": i}) for i in range(5)]

        # Process batch
        results = await service.embed_batch([data.text for data in batch])

        # Verify results
        assert len(results) == len(batch)
        assert all(r is not None for r in results)

        # Check metrics
        metrics = service._instrumentor._metrics.get_metrics("embed_batch")
        assert len(metrics) == 1
        assert metrics[0].metadata.get("batch_size") == len(batch)

    async def test_resource_aware_batch_processing(
        self, service: EmbeddingService, settings: Settings
    ):
        """Test resource-aware batch processing."""
        # Create large batch
        large_batch = [
            BatchTestData(text="test" * 1000, metadata={})
            for _ in range(settings.max_batch_size * 2)
        ]

        # Mock resource manager to track batch splits
        batch_sizes = []
        original_execute = service._resource_manager.execute_with_resources

        async def track_batch_size(operation, **kwargs):
            batch_sizes.append(kwargs.get("batch_size", 0))
            return await original_execute(operation, **kwargs)

        with patch.object(
            service._resource_manager,
            "execute_with_resources",
            side_effect=track_batch_size,
        ):
            results = await service.embed_batch([data.text for data in large_batch])

        # Verify results
        assert len(results) == len(large_batch)

        # Verify batch splitting
        assert all(size <= settings.max_batch_size for size in batch_sizes)
        assert all(size >= settings.min_batch_size for size in batch_sizes)

    async def test_batch_error_handling(self, service: EmbeddingService):
        """Test error handling during batch processing."""
        # Create batch with invalid items
        batch = [
            BatchTestData(text="valid1", metadata={}),
            BatchTestData(text="", metadata={}),  # Invalid
            BatchTestData(text="valid2", metadata={}),
            BatchTestData(text="   ", metadata={}),  # Invalid
        ]

        # Process batch with error collection
        with pytest.raises(ValidationError) as exc_info:
            await service.embed_batch([data.text for data in batch])

        # Verify error details
        assert "Invalid items in batch" in str(exc_info.value)
        assert len(exc_info.value.details.get("invalid_items", [])) == 2

        # Check error metrics
        metrics = service._instrumentor._metrics.get_metrics("embed_batch")
        assert any(
            "error" in m.metadata and "ValidationError" in m.metadata["error"] for m in metrics
        )

    async def test_concurrent_batch_processing(self, service: EmbeddingService):
        """Test concurrent batch processing."""
        # Create multiple batches
        batches = [
            [BatchTestData(text=f"batch{j}_item{i}", metadata={}) for i in range(5)]
            for j in range(3)
        ]

        # Process batches concurrently
        tasks = [service.embed_batch([data.text for data in batch]) for batch in batches]

        results = await asyncio.gather(*tasks)

        # Verify results
        assert len(results) == len(batches)
        assert all(len(r) == len(b) for r, b in zip(results, batches))

        # Check metrics
        metrics = service._instrumentor._metrics.get_metrics("embed_batch")
        assert len(metrics) == len(batches)
        assert all(m.metadata.get("batch_size") == len(batches[0]) for m in metrics)

    async def test_batch_size_optimization(self, service: EmbeddingService, settings: Settings):
        """Test batch size optimization based on resource usage."""
        # Create batch with varying text sizes
        batch = [
            BatchTestData(
                text="test" * (1000 * i),  # Increasing sizes
                metadata={},
                expected_size=50 // (i + 1),  # Expected batch size decreases
            )
            for i in range(1, 4)
        ]

        # Track actual batch sizes
        actual_sizes = []
        original_execute = service._resource_manager.execute_with_resources

        async def track_batch_size(operation, **kwargs):
            actual_sizes.append(kwargs.get("batch_size", 0))
            return await original_execute(operation, **kwargs)

        with patch.object(
            service._resource_manager,
            "execute_with_resources",
            side_effect=track_batch_size,
        ):
            await service.embed_batch([data.text for data in batch])

        # Verify batch size adaptation
        assert len(actual_sizes) > 0
        assert all(size <= settings.max_batch_size for size in actual_sizes)
        assert all(size >= settings.min_batch_size for size in actual_sizes)

        # Verify metrics
        metrics = service._instrumentor._metrics.get_metrics("embed_batch")
        memory_usage = [m.memory_mb for m in metrics]
        assert all(m2 >= m1 for m1, m2 in zip(memory_usage, memory_usage[1:]))

    async def test_batch_resource_limits(self, service: EmbeddingService, settings: Settings):
        """Test batch processing respects resource limits."""
        # Create batch that would exceed memory limits
        batch = [
            BatchTestData(text="test" * 1000000, metadata={})
            for _ in range(settings.max_batch_size)
        ]

        # Mock resource manager to simulate memory pressure
        with patch.object(service._resource_manager, "execute_with_resources") as mock_execute:
            mock_execute.side_effect = ResourceError("Memory limit exceeded")

            with pytest.raises(ResourceError) as exc_info:
                await service.embed_batch([data.text for data in batch])

        assert "Memory limit exceeded" in str(exc_info.value)

        # Verify metrics
        metrics = service._instrumentor._metrics.get_metrics("embed_batch")
        assert any(
            "error" in m.metadata and "ResourceError" in m.metadata["error"] for m in metrics
        )

    async def test_empty_batch_handling(self, service: EmbeddingService):
        """Test handling of empty batches."""
        # Test with empty batch
        with pytest.raises(ValidationError) as exc_info:
            await service.embed_batch([])

        assert "Empty batch" in str(exc_info.value)

        # Test with None
        with pytest.raises(ValidationError) as exc_info:
            await service.embed_batch(None)

        assert "Invalid batch" in str(exc_info.value)

    async def test_batch_retry_mechanism(self, service: EmbeddingService):
        """Test batch processing retry mechanism."""
        batch = [BatchTestData(text=f"test{i}", metadata={}) for i in range(5)]

        # Mock model to fail on first attempt
        with patch.object(service, "_model") as mock_model:
            mock_model.encode.side_effect = [
                RuntimeError("Temporary error"),
                ["result"] * len(batch),  # Succeed on retry
            ]

            results = await service.embed_batch([data.text for data in batch])

        assert len(results) == len(batch)

        # Verify retry metrics
        metrics = service._instrumentor._metrics.get_metrics("embed_batch")
        assert any("retry_count" in m.metadata and m.metadata["retry_count"] > 0 for m in metrics)
