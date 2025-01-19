"""Text and chunk processing package.

This package provides functionality for processing and normalizing text data,
as well as chunk processing operations.
"""

from .base import BaseProcessor
from .chunk import ChunkProcessor
from .models import (
    Chunk,
    ChunkBatch,
    ProcessedChunk,
    ProcessingContext,
    ProcessingMetadata,
    ProcessingStrategy,
    ServiceInitializationError,
    ServiceNotInitializedError,
    ServiceState,
    ValidationError,
)
from .text import TextProcessor


__all__ = [
    # Core processors
    "BaseProcessor",
    "ChunkProcessor",
    "TextProcessor",
    # Models
    "Chunk",
    "ChunkBatch",
    "ProcessedChunk",
    "ProcessingContext",
    "ProcessingMetadata",
    "ProcessingStrategy",
    # Error types
    "ServiceInitializationError",
    "ServiceNotInitializedError",
    "ValidationError",
    # Service types
    "ServiceState",
]
