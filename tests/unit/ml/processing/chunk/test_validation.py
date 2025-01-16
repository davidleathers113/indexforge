"""Tests for chunk validation functionality."""

import uuid

import pytest

from src.core.models.chunks import Chunk
from src.ml.processing.errors import ValidationError


def test_validate_valid_chunk(processor, sample_chunk):
    """Test validation of a valid chunk."""
    errors = processor.validate_chunk(sample_chunk)
    assert not errors


@pytest.mark.parametrize(
    "content,metadata,expected_error",
    [
        ("", None, "Chunk content cannot be empty"),
        ("   ", None, "Chunk content cannot be empty or whitespace only"),
        (None, None, "Chunk content must be a non-empty string"),
        ("Valid", "invalid", "Chunk metadata must be a dictionary or None"),
        (123, None, "Chunk content must be a non-empty string"),
    ],
)
def test_validate_invalid_chunks(processor, content, metadata, expected_error):
    """Test validation with various invalid chunks."""
    chunk = Chunk(
        id=uuid.uuid4(),
        content=content,
        metadata=metadata,
    )
    errors = processor.validate_chunk(chunk)
    assert expected_error in errors


def test_validate_invalid_type(processor):
    """Test validation with non-Chunk input."""
    with pytest.raises(TypeError) as exc_info:
        processor.validate_chunk("not a chunk")
    assert "Input must be a Chunk instance" in str(exc_info.value)


def test_process_invalid_chunk(processor, sample_chunk):
    """Test processing an invalid chunk raises ValidationError."""
    # Make the chunk invalid by clearing its content
    sample_chunk.content = ""

    with pytest.raises(ValidationError) as exc_info:
        processor.process_chunk(sample_chunk)
    assert "Chunk content cannot be empty" in str(exc_info.value)
