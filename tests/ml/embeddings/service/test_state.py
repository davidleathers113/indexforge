"""Tests for embedding service state management."""

from unittest.mock import patch

import pytest

from src.services.ml.entities import Chunk
from src.services.ml.implementations import EmbeddingParameters, EmbeddingService
from src.services.ml.service.errors import (
    ServiceInitializationError,
    ServiceNotInitializedError,
    ServiceStateError,
)
from tests.ml.embeddings.fixtures import EmbeddingServiceFactory


class TestStateTransitions:
    """Test suite for service state transitions."""

    @pytest.mark.asyncio
    async def test_initial_state(self) -> None:
        """Test initial service state."""
        service = EmbeddingServiceFactory.default()
        assert not service.is_initialized
        assert service.state.is_uninitialized

    @pytest.mark.asyncio
    async def test_initialization_success(self) -> None:
        """Test successful service initialization."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()
        assert service.is_initialized
        assert service.state.is_running
        await service.cleanup()

    @pytest.mark.asyncio
    async def test_cleanup_success(self) -> None:
        """Test successful service cleanup."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()
        await service.cleanup()
        assert not service.is_initialized
        assert service.state.is_stopped


class TestStateValidation:
    """Test suite for state validation rules."""

    @pytest.mark.asyncio
    async def test_double_initialization(self) -> None:
        """Test prevention of double initialization."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()

        with pytest.raises(ServiceStateError):
            await service.initialize()

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_cleanup_before_initialization(self) -> None:
        """Test prevention of cleanup before initialization."""
        service = EmbeddingServiceFactory.default()
        with pytest.raises(ServiceStateError):
            await service.cleanup()

    @pytest.mark.asyncio
    async def test_double_cleanup(self) -> None:
        """Test prevention of double cleanup."""
        service = EmbeddingServiceFactory.default()
        await service.initialize()
        await service.cleanup()

        with pytest.raises(ServiceStateError):
            await service.cleanup()


class TestStateRecovery:
    """Test suite for state recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_initialization_failure_recovery(self) -> None:
        """Test recovery from initialization failure."""
        # First try with invalid service
        service = EmbeddingServiceFactory.invalid()

        with pytest.raises(ServiceInitializationError):
            await service.initialize()

        assert service.state.is_error
        assert not service.is_initialized

        # Should be able to cleanup
        await service.cleanup()
        assert service.state.is_stopped

    @pytest.mark.asyncio
    async def test_reinitialization_after_cleanup(self) -> None:
        """Test reinitialization after cleanup."""
        service = EmbeddingServiceFactory.default()

        # First initialization
        await service.initialize()
        assert service.is_initialized

        # Cleanup
        await service.cleanup()
        assert not service.is_initialized

        # Should be able to initialize again
        await service.initialize()
        assert service.is_initialized
        assert service.state.is_running

        # Final cleanup
        await service.cleanup()

    @pytest.mark.asyncio
    async def test_model_loading_failure() -> None:
        """Test handling of model loading failures."""
        params = EmbeddingParameters(
            model_name="non-existent-model", batch_size=32, min_text_length=1, max_text_length=512
        )
        service = EmbeddingService(params)

        # Model loading should fail with invalid model name
        with pytest.raises(ServiceInitializationError) as exc_info:
            await service.initialize()

        assert "model" in str(exc_info.value).lower()
        assert not service.is_initialized
        assert service.state.is_error

        # Attempting operations should raise ServiceNotInitializedError
        with pytest.raises(ServiceNotInitializedError):
            await service.embed_chunk(Chunk(content="test", metadata={}))
