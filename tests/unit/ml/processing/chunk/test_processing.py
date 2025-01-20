"""Tests for chunk processing functionality.

Note: This test file is deprecated and will be removed in Phase 4 (Cleanup and Testing).
The functionality tested here has been migrated to the new service implementation,
with more comprehensive test coverage in tests/ml/processing/service/.

Key test coverage has been moved to:
- test_state.py: Service lifecycle and state management
- test_validation.py: Input validation and constraints
- test_recovery.py: Error handling and graceful degradation

This file is maintained temporarily to ensure backward compatibility
during the migration period.
"""

from unittest.mock import Mock

import pytest

from src.ml.processing.errors import ServiceStateError
from src.ml.processing.models.chunks import ProcessedChunk


def test_process_chunk(processor, sample_chunk, mock_nlp):
    """Test processing a single chunk."""
    # Setup mock strategy results
    mock_nlp.__call__.return_value = Mock(
        __iter__=Mock(return_value=iter([Mock(text="test")])),
        ents=[Mock(text="John Smith", label_="PERSON", start_char=0, end_char=10)],
        __len__=Mock(return_value=1),
    )

    result = processor.process_chunk(sample_chunk)

    assert isinstance(result, ProcessedChunk)
    assert result.id == sample_chunk.id
    assert result.content == sample_chunk.content
    assert result.metadata == sample_chunk.metadata
    assert len(result.tokens) > 0
    assert len(result.named_entities) > 0
    assert isinstance(result.sentiment_score, float)


def test_process_chunks(processor, sample_chunks, mock_nlp):
    """Test processing multiple chunks."""
    # Setup mock strategy results
    mock_nlp.__call__.return_value = Mock(
        __iter__=Mock(return_value=iter([Mock(text="test")])),
        ents=[],
        __len__=Mock(return_value=1),
    )

    results = processor.process_chunks(sample_chunks)

    assert len(results) == len(sample_chunks)
    for result, original in zip(results, sample_chunks, strict=False):
        assert isinstance(result, ProcessedChunk)
        assert result.id == original.id
        assert result.content == original.content


def test_process_without_initialization(settings, sample_chunk):
    """Test processing fails when processor is not initialized."""
    from src.ml.processing.chunk import ChunkProcessor

    processor = ChunkProcessor(settings)
    with pytest.raises(ServiceStateError) as exc_info:
        processor.process_chunk(sample_chunk)
    assert "Processor not initialized" in str(exc_info.value)


def test_process_with_metadata(processor, sample_chunk, mock_nlp):
    """Test processing with additional metadata."""
    # Setup mock strategy results
    mock_nlp.__call__.return_value = Mock(
        __iter__=Mock(return_value=iter([Mock(text="test")])),
        ents=[],
        __len__=Mock(return_value=1),
    )

    metadata = {"processing_config": {"use_gpu": True}}
    result = processor.process_chunk(sample_chunk, metadata)

    assert isinstance(result, ProcessedChunk)
    assert result.metadata == {**sample_chunk.metadata, **metadata}
