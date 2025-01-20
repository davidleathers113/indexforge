"""Tests for service state transitions.

This module verifies the state transition logic for ML services,
focusing on:
1. Initialization sequence
2. Error recovery paths
3. Resource exhaustion handling
4. Cleanup and shutdown
"""

import asyncio
from typing import Optional
from unittest.mock import Mock, patch

import pytest

from src.core.settings import Settings
from src.services.ml.errors import ModelLoadError, ResourceError, ServiceNotInitializedError
from src.services.ml.implementations.factories import ServiceFactory
from src.services.ml.monitoring.instrumentation import (
    InstrumentationConfig,
    PerformanceInstrumentor,
)
from src.services.ml.monitoring.metrics import MetricsCollector
from src.services.ml.optimization.resources import ResourceManager


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


class TestServiceStateTransitions:
    """Tests for service state transitions."""

    async def test_initialization_sequence(self, settings, instrumentor):
        """Test service initialization sequence."""
        # Create service without auto-initialization
        service = await ServiceFactory.create_embedding_service(settings, auto_init=False)
        service.set_instrumentor(instrumentor)

        # Verify initial state
        assert not service.is_initialized()

        # Initialize service
        await service.initialize()

        # Verify initialized state
        assert service.is_initialized()
        assert service._model is not None
        assert service._validator is not None

        # Verify initialization metrics
        metrics = service._instrumentor._metrics.get_metrics("initialize")
        assert len(metrics) > 0
        assert all(m.metadata.get("status") == "success" for m in metrics)

    async def test_initialization_failure(self, settings, instrumentor):
        """Test handling of initialization failures."""
        service = await ServiceFactory.create_embedding_service(settings, auto_init=False)
        service.set_instrumentor(instrumentor)

        # Mock model loading to fail
        with patch("src.services.ml.implementations.factories.ModelFactory") as mock_factory:
            mock_factory.load_model.side_effect = RuntimeError("Model load failed")

            # Attempt initialization
            with pytest.raises(ModelLoadError) as exc_info:
                await service.initialize()

            assert "Model load failed" in str(exc_info.value)
            assert not service.is_initialized()

            # Verify error metrics
            metrics = service._instrumentor._metrics.get_metrics("initialize")
            assert any(
                "error" in m.metadata and "Model load failed" in m.metadata["error"]
                for m in metrics
            )

    async def test_operation_state_requirements(self, settings, instrumentor):
        """Test state requirements for operations."""
        service = await ServiceFactory.create_embedding_service(settings, auto_init=False)
        service.set_instrumentor(instrumentor)

        # Attempt operation before initialization
        with pytest.raises(ServiceNotInitializedError):
            await service.embed_text("test")

        # Initialize and verify operation works
        await service.initialize()
        result = await service.embed_text("test")
        assert result is not None

    async def test_resource_exhaustion_recovery(self, settings, instrumentor):
        """Test recovery from resource exhaustion."""
        service = await ServiceFactory.create_embedding_service(settings)
        service.set_instrumentor(instrumentor)

        # Mock resource manager to simulate exhaustion
        with patch.object(service._resource_manager, "execute_with_resources") as mock_execute:
            # First call fails with resource error
            mock_execute.side_effect = [
                ResourceError("Memory limit exceeded"),
                "success",  # Second call succeeds
            ]

            # Attempt operation
            with pytest.raises(ResourceError):
                await service.embed_text("test")

            # Verify service is still in valid state
            assert service.is_initialized()

            # Retry operation
            result = await service.embed_text("test")
            assert result == "success"

    async def test_cleanup_sequence(self, settings, instrumentor):
        """Test service cleanup sequence."""
        service = await ServiceFactory.create_embedding_service(settings)
        service.set_instrumentor(instrumentor)

        # Perform some operations
        await service.embed_text("test")

        # Cleanup service
        await service.cleanup()

        # Verify cleanup
        assert not service.is_initialized()
        assert service._model is None
        assert service._validator is None

        # Verify cleanup metrics
        metrics = service._instrumentor._metrics.get_metrics("cleanup")
        assert len(metrics) > 0
        assert all(m.metadata.get("status") == "success" for m in metrics)

    async def test_concurrent_state_transitions(self, settings, instrumentor):
        """Test concurrent state transitions."""
        service = await ServiceFactory.create_embedding_service(settings, auto_init=False)
        service.set_instrumentor(instrumentor)

        # Attempt concurrent initialization
        init_tasks = [service.initialize() for _ in range(3)]
        await asyncio.gather(*init_tasks)

        # Verify only one initialization succeeded
        init_metrics = service._instrumentor._metrics.get_metrics("initialize")
        success_count = sum(1 for m in init_metrics if m.metadata.get("status") == "success")
        assert success_count == 1

        # Attempt concurrent cleanup
        cleanup_tasks = [service.cleanup() for _ in range(3)]
        await asyncio.gather(*cleanup_tasks)

        # Verify cleanup completed
        assert not service.is_initialized()

    async def test_error_recovery_paths(self, settings, instrumentor):
        """Test error recovery paths."""
        service = await ServiceFactory.create_embedding_service(settings)
        service.set_instrumentor(instrumentor)

        # Mock model to simulate various errors
        with patch.object(service, "_model") as mock_model:
            # Simulate temporary error
            mock_model.encode.side_effect = [
                RuntimeError("Temporary error"),
                "success",  # Second attempt succeeds
            ]

            # First attempt fails
            with pytest.raises(RuntimeError):
                await service.embed_text("test")

            # Verify service state remains valid
            assert service.is_initialized()

            # Second attempt succeeds
            result = await service.embed_text("test")
            assert result == "success"

    async def test_resource_state_management(self, settings, instrumentor):
        """Test resource state management."""
        service = await ServiceFactory.create_embedding_service(settings)
        service.set_instrumentor(instrumentor)

        # Track initial resource state
        initial_metrics = service._instrumentor._metrics.get_resource_metrics("embed_text")

        # Perform operation
        await service.embed_text("test")

        # Get updated resource metrics
        current_metrics = service._instrumentor._metrics.get_resource_metrics("embed_text")

        # Verify resource tracking
        assert len(current_metrics) > len(initial_metrics)
        assert all(m.memory_mb > 0 for m in current_metrics)
        assert all(m.cpu_percent >= 0 for m in current_metrics)

    async def test_state_persistence(self, settings, instrumentor):
        """Test state persistence across operations."""
        service = await ServiceFactory.create_embedding_service(settings)
        service.set_instrumentor(instrumentor)

        # Perform multiple operations
        texts = ["test1", "test2", "test3"]
        results = []

        for text in texts:
            result = await service.embed_text(text)
            results.append(result)

        # Verify state remained consistent
        assert service.is_initialized()
        assert all(r is not None for r in results)

        # Verify operation metrics show consistent state
        metrics = service._instrumentor._metrics.get_metrics("embed_text")
        assert len(metrics) == len(texts)
        assert all(m.metadata.get("status") == "success" for m in metrics)
