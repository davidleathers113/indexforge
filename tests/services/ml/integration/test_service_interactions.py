"""Integration tests for ML service interactions.

This module tests the interactions between different ML service components,
focusing on:
1. Service initialization and dependency injection
2. Resource management integration
3. Validation framework integration
4. Monitoring system integration
5. Error handling and recovery
"""

import asyncio
from typing import List
from unittest.mock import Mock, patch

import pytest
from pydantic import BaseModel

from src.core.settings import Settings
from src.services.ml.errors import InstrumentationError, ResourceError, ValidationError
from src.services.ml.implementations.embedding import EmbeddingService
from src.services.ml.implementations.factories import ServiceFactory
from src.services.ml.implementations.processing import ProcessingService
from src.services.ml.monitoring.instrumentation import (
    InstrumentationConfig,
    PerformanceInstrumentor,
)
from src.services.ml.monitoring.metrics import MetricsCollector
from src.services.ml.optimization.resources import ResourceManager


class TestData(BaseModel):
    """Test data model."""

    text: str
    metadata: dict


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        max_memory_mb=1000,
        batch_size=10,
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
async def embedding_service(settings, instrumentor):
    """Create embedding service."""
    service = await ServiceFactory.create_embedding_service(settings)
    service.set_instrumentor(instrumentor)
    return service


@pytest.fixture
async def processing_service(settings, instrumentor):
    """Create processing service."""
    service = await ServiceFactory.create_processing_service(settings)
    service.set_instrumentor(instrumentor)
    return service


class TestServiceInteractions:
    """Integration tests for service interactions."""

    async def test_service_initialization(
        self, embedding_service: EmbeddingService, processing_service: ProcessingService
    ):
        """Test service initialization and dependency injection."""
        # Verify services are properly initialized
        assert embedding_service.is_initialized()
        assert processing_service.is_initialized()

        # Check instrumentation setup
        assert embedding_service._instrumentor is not None
        assert processing_service._instrumentor is not None

    async def test_resource_management_integration(
        self, embedding_service: EmbeddingService, settings: Settings
    ):
        """Test resource management during operations."""
        # Create test data that would exceed memory limits
        large_batch = [TestData(text="test" * 1000000, metadata={}) for _ in range(100)]

        # Attempt to process large batch
        with pytest.raises(ResourceError) as exc_info:
            await embedding_service.embed_batch(large_batch)

        assert "Memory limit exceeded" in str(exc_info.value)

        # Verify metrics were recorded
        metrics = embedding_service._instrumentor._metrics.get_metrics("embed_batch")
        assert len(metrics) > 0
        assert any(m.metadata.get("error_type") == "ResourceError" for m in metrics)

    async def test_validation_integration(self, processing_service: ProcessingService):
        """Test validation framework integration."""
        # Test with invalid input
        invalid_data = TestData(text="", metadata={"invalid": True})

        with pytest.raises(ValidationError) as exc_info:
            await processing_service.process_text(invalid_data)

        assert "Validation failed" in str(exc_info.value)

        # Test with valid input
        valid_data = TestData(text="Valid test input", metadata={"valid": True})
        result = await processing_service.process_text(valid_data)
        assert result is not None

    async def test_monitoring_integration(
        self, embedding_service: EmbeddingService, processing_service: ProcessingService
    ):
        """Test monitoring system integration."""
        test_data = TestData(text="Test monitoring", metadata={})

        # Perform operations on both services
        await embedding_service.embed_text(test_data)
        await processing_service.process_text(test_data)

        # Verify metrics were collected for both services
        embed_metrics = embedding_service._instrumentor._metrics.get_metrics("embed_text")
        process_metrics = processing_service._instrumentor._metrics.get_metrics("process_text")

        assert len(embed_metrics) > 0
        assert len(process_metrics) > 0

        # Check resource tracking
        assert all(m.memory_mb > 0 for m in embed_metrics)
        assert all(m.duration_ms > 0 for m in process_metrics)

    async def test_error_handling_integration(self, embedding_service: EmbeddingService):
        """Test error handling and recovery across components."""
        # Mock model to simulate errors
        with patch.object(embedding_service, "_model") as mock_model:
            mock_model.encode.side_effect = RuntimeError("Model error")

            # Attempt operation that will fail
            with pytest.raises(InstrumentationError) as exc_info:
                await embedding_service.embed_text(
                    TestData(text="Test error handling", metadata={})
                )

            assert "Model error" in str(exc_info.value)

            # Verify error was recorded in metrics
            metrics = embedding_service._instrumentor._metrics.get_metrics("embed_text")
            assert any(
                "error" in m.metadata and "Model error" in m.metadata["error"] for m in metrics
            )

    async def test_concurrent_operations(
        self, embedding_service: EmbeddingService, processing_service: ProcessingService
    ):
        """Test concurrent operations across services."""
        test_data = [TestData(text=f"Test {i}", metadata={}) for i in range(5)]

        # Run operations concurrently
        embedding_tasks = [embedding_service.embed_text(data) for data in test_data]
        processing_tasks = [processing_service.process_text(data) for data in test_data]

        # Wait for all operations to complete
        await asyncio.gather(
            *embedding_tasks,
            *processing_tasks,
        )

        # Verify all operations were tracked
        embed_metrics = embedding_service._instrumentor._metrics.get_metrics("embed_text")
        process_metrics = processing_service._instrumentor._metrics.get_metrics("process_text")

        assert len(embed_metrics) == len(test_data)
        assert len(process_metrics) == len(test_data)

    async def test_resource_cleanup(
        self, embedding_service: EmbeddingService, processing_service: ProcessingService
    ):
        """Test resource cleanup after operations."""
        # Perform operations
        test_data = TestData(text="Test cleanup", metadata={})
        await embedding_service.embed_text(test_data)
        await processing_service.process_text(test_data)

        # Cleanup services
        await embedding_service.cleanup()
        await processing_service.cleanup()

        # Verify resources were released
        assert not embedding_service.is_initialized()
        assert not processing_service.is_initialized()

        # Verify metrics were recorded
        metrics = embedding_service._instrumentor._metrics.get_metrics("cleanup")
        assert len(metrics) > 0
        assert all(m.metadata.get("status") == "success" for m in metrics)
