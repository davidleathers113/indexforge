"""Chunk model definitions for text processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

import numpy as np
from numpy.typing import NDArray

from .base import ProcessingContext, ProcessingMetadata


@dataclass
class Chunk:
    """A chunk of text content for processing.

    This class represents a unit of text content that can be
    processed by various strategies.

    Attributes:
        id: Unique identifier for the chunk
        content: Text content of the chunk
        metadata: Optional chunk metadata
        context: Processing context
    """

    id: UUID = field(default_factory=uuid4)
    content: str = field(default="")
    metadata: dict[str, Any] | None = field(default=None)
    context: ProcessingContext = field(default_factory=ProcessingContext)

    def __post_init__(self) -> None:
        """Validate chunk after initialization."""
        if not isinstance(self.content, str):
            raise TypeError("Content must be a string")
        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise TypeError("Metadata must be a dictionary or None")


@dataclass
class ProcessedChunk:
    """A processed chunk with analysis results.

    This class represents a chunk that has been processed by
    various strategies, containing the analysis results.

    Attributes:
        id: Original chunk identifier
        content: Original text content
        metadata: Original chunk metadata
        tokens: Tokenization results
        named_entities: Named entity recognition results
        sentiment_score: Sentiment analysis score
        topic_id: Topic identification result
        embedding: Vector embedding of content
        processing_metadata: Metadata about the processing
    """

    id: UUID
    content: str
    metadata: dict[str, Any] | None = None
    tokens: list[str] = field(default_factory=list)
    named_entities: list[dict[str, Any]] = field(default_factory=list)
    sentiment_score: float = 0.0
    topic_id: str | None = None
    embedding: NDArray[np.float32] | None = None
    processing_metadata: ProcessingMetadata = field(default_factory=ProcessingMetadata)

    def __post_init__(self) -> None:
        """Validate processed chunk after initialization."""
        if not isinstance(self.tokens, list):
            raise TypeError("Tokens must be a list")
        if not isinstance(self.named_entities, list):
            raise TypeError("Named entities must be a list")
        if not isinstance(self.sentiment_score, (int, float)):
            raise TypeError("Sentiment score must be numeric")
        if self.topic_id is not None and not isinstance(self.topic_id, str):
            raise TypeError("Topic ID must be a string or None")
        if self.embedding is not None and not isinstance(self.embedding, np.ndarray):
            raise TypeError("Embedding must be a numpy array or None")


@dataclass
class ChunkBatch:
    """A batch of chunks for processing.

    This class represents a collection of chunks that should
    be processed together.

    Attributes:
        chunks: List of chunks in the batch
        metadata: Optional batch metadata
        context: Processing context for the batch
    """

    chunks: list[Chunk] = field(default_factory=list)
    metadata: dict[str, Any] | None = field(default=None)
    context: ProcessingContext = field(default_factory=ProcessingContext)

    def __post_init__(self) -> None:
        """Validate batch after initialization."""
        if not isinstance(self.chunks, list):
            raise TypeError("Chunks must be a list")
        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise TypeError("Metadata must be a dictionary or None")

    def add_chunk(self, chunk: Chunk) -> None:
        """Add a chunk to the batch.

        Args:
            chunk: Chunk to add

        Raises:
            TypeError: If chunk is invalid
        """
        if not isinstance(chunk, Chunk):
            raise TypeError("Input must be a Chunk instance")
        self.chunks.append(chunk)

    def get_chunk(self, chunk_id: UUID) -> Chunk | None:
        """Get a chunk by its ID.

        Args:
            chunk_id: ID of chunk to retrieve

        Returns:
            Chunk if found, None otherwise
        """
        for chunk in self.chunks:
            if chunk.id == chunk_id:
                return chunk
        return None
