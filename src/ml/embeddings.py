"""Embeddings generation module.

This module provides functionality for generating embeddings from text using
sentence transformers.
"""

from dataclasses import asdict
from datetime import datetime
from typing import TYPE_CHECKING, Any

import numpy as np
import numpy.typing as npt


try:
    from sentence_transformers import SentenceTransformer

    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False

from src.core import BaseService, Chunk, ChunkEmbedder, ChunkMetadata, ProcessedChunk
from src.ml.processing.models.service import (
    ServiceInitializationError,
    ServiceNotInitializedError,
    ServiceState,
    ServiceStateError,
)


if TYPE_CHECKING:
    from src.core.settings import Settings


class EmbeddingGenerator(BaseService, ChunkEmbedder):
    """Generate embeddings from text using sentence transformers.

    Implements the ChunkEmbedder interface for generating vector embeddings
    from text chunks using sentence transformers.
    """

    # Constants for chunk size validation
    MIN_CHUNK_SIZE = 1024  # 1KB
    MAX_CHUNK_SIZE = 1024 * 1024  # 1MB
    MIN_WORDS = 3  # Minimum words for semantic meaning

    def __init__(self, settings: "Settings") -> None:
        """Initialize the embedding generator.

        Args:
            settings: Application settings

        Raises:
            ValueError: If required settings are missing
        """
        if not settings.embedding_model:
            raise ValueError("embedding_model setting is required")
        if not settings.batch_size or settings.batch_size <= 0:
            raise ValueError("batch_size must be a positive integer")

        BaseService.__init__(self)
        ChunkEmbedder.__init__(self, settings)
        self._settings = settings
        self._model: SentenceTransformer | None = None
        self._batch_size = self._settings.batch_size

    async def initialize(self) -> None:
        """Initialize the embedding model.

        Raises:
            RuntimeError: If sentence transformers is not available
            ServiceInitializationError: If initialization fails
        """
        if not EMBEDDING_AVAILABLE:
            raise RuntimeError("sentence-transformers not installed")

        self._transition_state(ServiceState.INITIALIZING)
        try:
            self._model = SentenceTransformer(self._settings.embedding_model)
            self._start_time = datetime.now()
            self._initialized = True
            self._transition_state(ServiceState.RUNNING)
            self.add_metadata("model_name", self._settings.embedding_model)
            self.add_metadata("batch_size", self._batch_size)
        except Exception as e:
            self._transition_state(ServiceState.ERROR)
            raise ServiceInitializationError(f"Failed to initialize embedding model: {e!s}") from e

    async def cleanup(self) -> None:
        """Clean up resources.

        Raises:
            ServiceStateError: If cleanup fails
        """
        self._transition_state(ServiceState.STOPPING)
        try:
            self._model = None
            self._transition_state(ServiceState.STOPPED)
        except Exception as e:
            self._transition_state(ServiceState.ERROR)
            raise ServiceStateError(f"Failed to cleanup: {e!s}") from e

    def _validate_semantic_chunk(self, chunk: Chunk) -> list[str]:
        """Validate semantic properties of the chunk.

        Args:
            chunk: Chunk to validate

        Returns:
            List of validation error messages
        """
        errors = []
        if not chunk.content.strip():
            errors.append("Chunk content is empty or whitespace")

        word_count = len(chunk.content.split())
        if word_count < self.MIN_WORDS:
            errors.append(f"Chunk contains fewer than {self.MIN_WORDS} words")

        content_bytes = len(chunk.content.encode("utf-8"))
        if content_bytes < self.MIN_CHUNK_SIZE:
            errors.append(
                f"Chunk size ({content_bytes} bytes) is below minimum {self.MIN_CHUNK_SIZE} bytes"
            )
        if content_bytes > self.MAX_CHUNK_SIZE:
            errors.append(
                f"Chunk size ({content_bytes} bytes) exceeds maximum {self.MAX_CHUNK_SIZE} bytes"
            )

        return errors

    def _create_processed_chunk(
        self, chunk: Chunk, embedding: np.ndarray, metadata: dict[str, Any] | None = None
    ) -> ProcessedChunk:
        """Create a ProcessedChunk from a Chunk and its embedding.

        Args:
            chunk: Source chunk
            embedding: Generated embedding
            metadata: Optional processing metadata

        Returns:
            Processed chunk with embedding

        Raises:
            ValueError: If chunk validation fails
            TypeError: If chunk is not of correct type
        """
        if not isinstance(chunk, Chunk):
            raise TypeError("Input must be a Chunk instance")

        # Validate chunk before processing
        validation_errors = self._validate_semantic_chunk(chunk)
        if validation_errors:
            raise ValueError(f"Chunk validation failed: {'; '.join(validation_errors)}")

        # Create a new processed chunk inheriting from the base chunk
        chunk_dict = asdict(chunk)
        chunk_dict["embedding"] = embedding

        # Add any additional metadata
        if metadata:
            if not isinstance(chunk_dict["metadata"], dict):
                chunk_dict["metadata"] = {}
            chunk_dict["metadata"].update(metadata)

        return ProcessedChunk(
            **chunk_dict,
            tokens=[],  # Embedding service doesn't handle tokenization
            named_entities=[],  # Embedding service doesn't handle NER
            sentiment_score=None,  # Not handled by embedding service
            topic_id=None,  # Not handled by embedding service
        )

    def embed_chunk(
        self, chunk: Chunk, metadata: dict[str, Any] | None = None
    ) -> npt.NDArray[np.float32]:
        """Generate embedding for a chunk.

        Args:
            chunk: Chunk to embed
            metadata: Optional embedding metadata

        Returns:
            Vector embedding of chunk content

        Raises:
            ServiceStateError: If service is not initialized or not running
            ValueError: If chunk is invalid
            TypeError: If chunk is not of correct type
        """
        if not isinstance(chunk, Chunk):
            raise TypeError("Input must be a Chunk instance")

        self._check_running()
        if self._model is None:
            raise ServiceNotInitializedError("Model not initialized")

        # Validate chunk
        validation_errors = self.validate_chunk(chunk)
        if validation_errors:
            raise ValueError(f"Chunk validation failed: {'; '.join(validation_errors)}")

        # Add metadata to service metrics if provided
        if metadata:
            self.add_metadata("last_embedding_metadata", metadata)

        return self._model.encode(chunk.content, batch_size=self._batch_size)

    def embed_chunks(
        self, chunks: list[Chunk], metadata: dict[str, Any] | None = None
    ) -> list[npt.NDArray[np.float32]]:
        """Generate embeddings for multiple chunks.

        Args:
            chunks: Chunks to embed
            metadata: Optional embedding metadata

        Returns:
            List[np.ndarray]: List of vector embeddings

        Raises:
            ServiceStateError: If service is not initialized or not running
            ValueError: If any chunk is invalid
            TypeError: If any chunk is not of correct type
        """
        if not all(isinstance(chunk, Chunk) for chunk in chunks):
            raise TypeError("All inputs must be Chunk instances")

        self._check_running()
        if self._model is None:
            raise ServiceNotInitializedError("Model not initialized")

        # Validate all chunks first
        for chunk in chunks:
            validation_errors = self.validate_chunk(chunk)
            if validation_errors:
                raise ValueError(
                    f"Chunk validation failed for {chunk.id}: {'; '.join(validation_errors)}"
                )

        # Add metadata to service metrics if provided
        if metadata:
            self.add_metadata("last_batch_embedding_metadata", metadata)
            self.add_metadata("last_batch_size", len(chunks))

        # Optimize batch processing by encoding all texts at once
        texts = [chunk.content for chunk in chunks]
        return self._model.encode(texts, batch_size=self._batch_size)

    def validate_chunk(self, chunk: Chunk) -> list[str]:
        """Validate a chunk before processing.

        Args:
            chunk: Chunk to validate

        Returns:
            List of validation error messages

        Raises:
            TypeError: If chunk is not of correct type
        """
        if not isinstance(chunk, Chunk):
            raise TypeError("Input must be a Chunk instance")

        errors = []

        # Basic validation
        if not chunk.content:
            errors.append("Chunk content is empty")
        if not isinstance(chunk.metadata, ChunkMetadata):
            errors.append("Invalid chunk metadata")

        # Semantic validation
        errors.extend(self._validate_semantic_chunk(chunk))

        return errors
