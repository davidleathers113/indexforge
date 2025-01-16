"""Model definitions for text processing."""

from .base import ProcessingContext, ProcessingMetadata
from .chunks import Chunk, ChunkBatch, ProcessedChunk
from .errors import ServiceInitializationError, ServiceNotInitializedError, ValidationError
from .service import ServiceState
from .strategies import (
    NERResult,
    ProcessingStrategy,
    SentimentResult,
    StrategyResult,
    TokenizationResult,
    TopicResult,
)

__all__ = [
    # Base models
    "ProcessingContext",
    "ProcessingMetadata",
    # Chunk models
    "Chunk",
    "ChunkBatch",
    "ProcessedChunk",
    # Error classes
    "ServiceInitializationError",
    "ServiceNotInitializedError",
    "ValidationError",
    # Service models
    "ServiceState",
    # Strategy models
    "ProcessingStrategy",
    "StrategyResult",
    "TokenizationResult",
    "NERResult",
    "SentimentResult",
    "TopicResult",
]
