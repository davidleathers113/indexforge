"""Tests for chunk processor initialization and lifecycle."""

from unittest.mock import patch

import pytest

from src.core.errors import ServiceInitializationError, ServiceState


def test_init_without_spacy(settings):
    """Test initialization fails when spaCy is not available."""
    with patch("src.ml.processing.chunk.SPACY_AVAILABLE", False):
        from src.ml.processing.chunk import ChunkProcessor

        processor = ChunkProcessor(settings)
        with pytest.raises(ServiceInitializationError) as exc_info:
            processor.initialize()
        assert "spaCy is required" in str(exc_info.value)
        assert processor._state == ServiceState.ERROR


def test_init_with_invalid_settings():
    """Test initialization fails with invalid settings."""
    from src.ml.processing.chunk import ChunkProcessor

    with pytest.raises(ValueError):
        ChunkProcessor(None)


def test_initialize_loads_model(mock_spacy, settings):
    """Test initialization loads spaCy model."""
    from src.ml.processing.chunk import ChunkProcessor

    processor = ChunkProcessor(settings)
    processor.initialize()

    mock_spacy.load.assert_called_once_with("en_core_web_sm")
    assert processor._state == ServiceState.RUNNING


def test_initialize_handles_load_error(mock_spacy, settings):
    """Test initialization handles model loading errors."""
    mock_spacy.load.side_effect = Exception("Model load failed")
    from src.ml.processing.chunk import ChunkProcessor

    processor = ChunkProcessor(settings)
    with pytest.raises(ServiceInitializationError) as exc_info:
        processor.initialize()
    assert "Failed to initialize NLP components" in str(exc_info.value)
    assert processor._state == ServiceState.ERROR


def test_cleanup(processor):
    """Test cleanup properly stops the processor."""
    processor.cleanup()
    assert processor._state == ServiceState.STOPPED
    assert not processor._strategies  # Strategies should be cleared


def test_complete_lifecycle(settings, mock_spacy, sample_chunk):
    """Test complete processor lifecycle."""
    from src.ml.processing.chunk import ChunkProcessor

    # Create and verify initial state
    processor = ChunkProcessor(settings)
    assert processor._state == ServiceState.CREATED

    # Initialize and verify running state
    processor.initialize()
    assert processor._state == ServiceState.RUNNING

    # Process a chunk to verify functionality
    processed = processor.process_chunk(sample_chunk)
    assert processed.id == sample_chunk.id
    assert processed.content == sample_chunk.content

    # Cleanup and verify stopped state
    processor.cleanup()
    assert processor._state == ServiceState.STOPPED
