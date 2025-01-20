"""Processing types package.

This package provides types for processing operations, including:
- Processing protocols
- Processing states
- Processing errors
- Validation types
"""

from .errors import (
    ProcessingError,
    ProcessingStateError,
    ProcessingTimeout,
    ResourceError,
    ValidationError,
)
from .operations import ChunkEmbedder, ChunkProcessor, ChunkTransformer, TextProcessor
from .states import ProcessingStatus
from .validation import ChunkValidator

__all__ = [
    # Errors
    "ProcessingError",
    "ProcessingStateError",
    "ProcessingTimeout",
    "ResourceError",
    "ValidationError",
    # Operations
    "ChunkEmbedder",
    "ChunkProcessor",
    "ChunkTransformer",
    "TextProcessor",
    # States
    "ProcessingStatus",
    # Validation
    "ChunkValidator",
]
