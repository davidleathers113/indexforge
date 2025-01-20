"""Tests for processing service state management."""

import pytest

from src.services.ml.errors import (
    ServiceInitializationError,
    ServiceNotInitializedError,
    ServiceStateError,
)
from src.services.ml.implementations import ProcessingService
from src.services.ml.implementations.processing import ProcessingParameters


@pytest.fixture
def processing_service():
    """Create a processing service instance for testing."""
    return ProcessingService(
        ProcessingParameters(
            model_name="en_core_web_sm",
            min_text_length=10,
            max_text_length=1000000,
            min_words=3,
        )
    )


@pytest.mark.asyncio
async def test_initial_state(processing_service):
    """Test service starts in uninitialized state."""
    assert not processing_service.is_initialized
    assert not processing_service.is_running


@pytest.mark.asyncio
async def test_initialization_success(processing_service):
    """Test successful service initialization."""
    await processing_service.initialize()
    assert processing_service.is_initialized
    assert processing_service.is_running


@pytest.mark.asyncio
async def test_double_initialization(processing_service):
    """Test initializing an already initialized service."""
    await processing_service.initialize()
    await processing_service.initialize()  # Should log warning but not error
    assert processing_service.is_initialized
    assert processing_service.is_running


@pytest.mark.asyncio
async def test_cleanup_from_initialized(processing_service):
    """Test cleanup from initialized state."""
    await processing_service.initialize()
    await processing_service.cleanup()
    assert not processing_service.is_initialized
    assert not processing_service.is_running


@pytest.mark.asyncio
async def test_cleanup_from_uninitialized(processing_service):
    """Test cleanup from uninitialized state."""
    await processing_service.cleanup()  # Should not raise
    assert not processing_service.is_initialized
    assert not processing_service.is_running


@pytest.mark.asyncio
async def test_operations_require_initialization(processing_service):
    """Test operations fail when service not initialized."""
    with pytest.raises(ServiceNotInitializedError):
        await processing_service.process_chunk({"id": "test", "content": "test content"})


@pytest.mark.asyncio
async def test_state_after_failed_initialization(processing_service, monkeypatch):
    """Test service state after initialization failure."""

    def mock_load(*args, **kwargs):
        raise RuntimeError("Model load failed")

    monkeypatch.setattr("spacy.load", mock_load)

    with pytest.raises(ServiceInitializationError):
        await processing_service.initialize()

    assert not processing_service.is_initialized
    assert not processing_service.is_running


@pytest.mark.asyncio
async def test_cleanup_after_error(processing_service, monkeypatch):
    """Test cleanup after service enters error state."""

    def mock_load(*args, **kwargs):
        raise RuntimeError("Model load failed")

    monkeypatch.setattr("spacy.load", mock_load)

    try:
        await processing_service.initialize()
    except ServiceInitializationError:
        pass

    await processing_service.cleanup()
    assert not processing_service.is_initialized
    assert not processing_service.is_running
