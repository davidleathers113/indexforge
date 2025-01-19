"""Embedding operations implementation.

This module handles the core embedding operations, including validation
and generation of embeddings for chunks.
"""

from typing import Any, List, Optional

import numpy as np
import numpy.typing as npt

from src.core import Chunk

from .base import EmbeddingGenerator
from .errors import GeneratorError, ValidationError
from .metrics import batch_metrics, track_metrics
from .validation.composite import CompositeValidator


class EmbeddingOperations:
    """Handles core embedding operations."""

    def __init__(self, generator: EmbeddingGenerator, validator: CompositeValidator) -> None:
        """Initialize embedding operations.

        Args:
            generator: The embedding generator instance
            validator: The validator for chunks
        """
        self._generator = generator
        self._validator = validator

    @track_metrics("embed_chunk")
    def embed_chunk(
        self, chunk: Chunk, metadata: Optional[dict[str, Any]] = None
    ) -> npt.NDArray[np.float32]:
        """Generate embedding for a chunk.

        Args:
            chunk: The chunk to embed
            metadata: Optional metadata to track

        Returns:
            The generated embedding vector

        Raises:
            ValidationError: If chunk validation fails
            GeneratorError: If embedding generation fails
        """
        validation_errors = self._validator.validate(chunk)
        if validation_errors:
            raise ValidationError("Chunk validation failed", validation_errors, chunk_id=chunk.id)

        try:
            return self._generator.generate_embeddings([chunk.content])[0]
        except Exception as e:
            raise GeneratorError(
                "Failed to generate embedding",
                model_name=self._generator.__class__.__name__,
                batch_size=1,
            ) from e

    @track_metrics("embed_chunks")
    @batch_metrics()
    def embed_chunks(
        self, chunks: List[Chunk], metadata: Optional[dict[str, Any]] = None
    ) -> List[npt.NDArray[np.float32]]:
        """Generate embeddings for multiple chunks.

        Args:
            chunks: The chunks to embed
            metadata: Optional metadata to track

        Returns:
            List of generated embedding vectors

        Raises:
            TypeError: If chunks contains invalid items
            ValidationError: If any chunk validation fails
            GeneratorError: If batch embedding generation fails
        """
        if not all(isinstance(chunk, Chunk) for chunk in chunks):
            raise TypeError("All inputs must be Chunk instances")

        # Validate all chunks first
        for chunk in chunks:
            validation_errors = self._validator.validate(chunk)
            if validation_errors:
                raise ValidationError(
                    "Chunk validation failed", validation_errors, chunk_id=chunk.id
                )

        try:
            texts = [chunk.content for chunk in chunks]
            return list(self._generator.generate_embeddings(texts))
        except Exception as e:
            raise GeneratorError(
                "Failed to generate batch embeddings",
                model_name=self._generator.__class__.__name__,
                batch_size=len(chunks),
            ) from e
