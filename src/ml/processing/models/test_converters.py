"""Tests for model conversion utilities."""

from uuid import uuid4

import numpy as np

from src.core.models.chunks import Chunk as CoreChunk
from src.core.models.chunks import ChunkMetadata as CoreMetadata

from .chunks import Chunk as MLChunk
from .chunks import ProcessedChunk
from .converters import core_to_ml_chunk, ml_to_core_chunk


def test_core_to_ml_chunk_conversion():
    """Test converting core chunk to ML chunk."""
    # Create a core chunk
    core_metadata = CoreMetadata(
        content_type="text/plain",
        language="en",
        source_file="test.txt",
        line_numbers=(1, 10),
        custom_metadata={"key": "value"},
    )
    core_chunk = CoreChunk(
        content="Test content",
        metadata=core_metadata,
        id=uuid4(),
    )

    # Convert to ML chunk
    ml_chunk = core_to_ml_chunk(core_chunk)

    # Verify conversion
    assert isinstance(ml_chunk, MLChunk)
    assert ml_chunk.id == core_chunk.id
    assert ml_chunk.content == core_chunk.content
    assert ml_chunk.metadata is not None
    assert ml_chunk.metadata["content_type"] == core_metadata.content_type
    assert ml_chunk.metadata["language"] == core_metadata.language
    assert ml_chunk.metadata["source_file"] == core_metadata.source_file
    assert ml_chunk.metadata["line_numbers"] == core_metadata.line_numbers
    assert ml_chunk.metadata["key"] == "value"


def test_ml_to_core_chunk_basic_conversion():
    """Test converting ML chunk to core chunk."""
    # Create an ML chunk
    chunk_id = uuid4()
    ml_metadata = {
        "content_type": "text/plain",
        "language": "en",
        "source_file": "test.txt",
        "line_numbers": (1, 10),
        "custom_key": "custom_value",
    }
    ml_chunk = MLChunk(
        id=chunk_id,
        content="Test content",
        metadata=ml_metadata,
    )

    # Convert to core chunk
    core_chunk = ml_to_core_chunk(ml_chunk)

    # Verify conversion
    assert isinstance(core_chunk, CoreChunk)
    assert core_chunk.id == chunk_id
    assert core_chunk.content == ml_chunk.content
    assert core_chunk.metadata.content_type == ml_metadata["content_type"]
    assert core_chunk.metadata.language == ml_metadata["language"]
    assert core_chunk.metadata.source_file == ml_metadata["source_file"]
    assert core_chunk.metadata.line_numbers == ml_metadata["line_numbers"]
    assert core_chunk.metadata.custom_metadata["custom_key"] == "custom_value"
    assert core_chunk.ml_processed is None


def test_processed_chunk_to_core_conversion():
    """Test converting processed chunk to core chunk."""
    # Create a processed chunk
    chunk_id = uuid4()
    ml_metadata = {"content_type": "text/plain"}
    processed_chunk = ProcessedChunk(
        id=chunk_id,
        content="Test content",
        metadata=ml_metadata,
        tokens=["test", "content"],
        named_entities=[{"text": "test", "label": "TEST"}],
        sentiment_score=0.8,
        topic_id="topic_1",
        embedding=np.array([0.1, 0.2, 0.3], dtype=np.float32),
    )

    # Convert to core chunk
    core_chunk = ml_to_core_chunk(processed_chunk)

    # Verify conversion
    assert isinstance(core_chunk, CoreChunk)
    assert core_chunk.id == chunk_id
    assert core_chunk.content == processed_chunk.content
    assert core_chunk.ml_processed == processed_chunk


def test_metadata_handling():
    """Test edge cases in metadata handling."""
    # Test with minimal metadata
    ml_chunk = MLChunk(id=uuid4(), content="Test", metadata={"content_type": "text/plain"})
    core_chunk = ml_to_core_chunk(ml_chunk)
    assert core_chunk.metadata.language is None
    assert core_chunk.metadata.source_file is None
    assert core_chunk.metadata.line_numbers is None

    # Test with None metadata
    ml_chunk = MLChunk(id=uuid4(), content="Test", metadata=None)
    core_chunk = ml_to_core_chunk(ml_chunk)
    assert core_chunk.metadata.content_type == "text/plain"  # Default value
