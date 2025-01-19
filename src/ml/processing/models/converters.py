"""Model conversion utilities.

This module provides utilities for converting between core and ML models,
ensuring type safety and maintaining data integrity during conversions.
"""

from __future__ import annotations

from typing import Any

from src.core.models.chunks import Chunk as CoreChunk
from src.core.models.chunks import ChunkMetadata as CoreMetadata

from .base import ProcessingContext
from .chunks import Chunk as MLChunk
from .chunks import ProcessedChunk


def core_to_ml_chunk(core_chunk: CoreChunk) -> MLChunk:
    """Convert a core chunk to an ML chunk.

    Args:
        core_chunk: Core chunk model instance

    Returns:
        MLChunk: Converted ML chunk model
    """
    # Convert core metadata to ML metadata dictionary
    ml_metadata: dict[str, Any] = {
        "content_type": core_chunk.metadata.content_type,
        "language": core_chunk.metadata.language,
        "source_file": core_chunk.metadata.source_file,
        "line_numbers": core_chunk.metadata.line_numbers,
        **core_chunk.metadata.custom_metadata,
    }

    return MLChunk(
        id=core_chunk.id,
        content=core_chunk.content,
        metadata=ml_metadata,
        context=ProcessingContext(),
    )


def ml_to_core_chunk(ml_chunk: MLChunk | ProcessedChunk) -> CoreChunk:
    """Convert an ML chunk to a core chunk.

    Args:
        ml_chunk: ML chunk or processed chunk model instance

    Returns:
        CoreChunk: Converted core chunk model
    """
    # Extract base metadata fields
    core_metadata = CoreMetadata(
        content_type=ml_chunk.metadata.get("content_type", "text/plain"),
        language=ml_chunk.metadata.get("language"),
        source_file=ml_chunk.metadata.get("source_file"),
        line_numbers=ml_chunk.metadata.get("line_numbers"),
    )

    # Add any remaining metadata as custom fields
    reserved_fields = {"content_type", "language", "source_file", "line_numbers"}
    if ml_chunk.metadata:
        core_metadata.custom_metadata.update(
            {k: v for k, v in ml_chunk.metadata.items() if k not in reserved_fields}
        )

    # Create core chunk
    core_chunk = CoreChunk(
        id=ml_chunk.id,
        content=ml_chunk.content,
        metadata=core_metadata,
        references=[],  # References must be managed separately
    )

    # If this is a processed chunk, link it
    if isinstance(ml_chunk, ProcessedChunk):
        core_chunk.ml_processed = ml_chunk

    return core_chunk
