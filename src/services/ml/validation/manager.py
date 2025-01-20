"""Validation management for ML services.

This module provides validation management and coordination.
"""

import logging
from typing import Any, Dict, List, Optional

from src.core.models.chunks import Chunk
from src.services.ml.errors import ValidationError

from .parameters import BatchValidationParameters, ValidationParameters
from .strategies import ChunkValidationStrategy

logger = logging.getLogger(__name__)


class CompositeValidator:
    """Manages validation operations for services."""

    def __init__(
        self,
        validation_params: ValidationParameters,
        batch_params: BatchValidationParameters,
    ) -> None:
        """Initialize validation manager.

        Args:
            validation_params: Validation parameters
            batch_params: Batch validation parameters
        """
        self._validation_params = validation_params
        self._batch_params = batch_params
        self._chunk_validator = ChunkValidationStrategy()

    def validate_chunk(self, chunk: Chunk, context: Optional[Dict[str, Any]] = None) -> None:
        """Validate a single chunk.

        Args:
            chunk: Chunk to validate
            context: Optional validation context

        Raises:
            ValidationError: If validation fails
        """
        errors = self._chunk_validator.validate(chunk, self._validation_params)
        if errors:
            logger.warning(f"Validation failed for chunk {chunk.id}: {errors}")
            raise ValidationError("\n".join(errors))

    def validate_chunks(
        self, chunks: List[Chunk], context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Validate multiple chunks.

        Args:
            chunks: Chunks to validate
            context: Optional validation context

        Raises:
            ValidationError: If validation fails
        """
        if not chunks:
            raise ValidationError("Empty chunk list")

        # Validate batch constraints
        batch_errors = []
        if len(chunks) > self._batch_params.max_batch_size:
            batch_errors.append(
                f"Batch size {len(chunks)} exceeds maximum {self._batch_params.max_batch_size}"
            )
        if batch_errors:
            raise ValidationError("\n".join(batch_errors))

        # Validate individual chunks
        for chunk in chunks:
            try:
                self.validate_chunk(chunk, context)
            except ValidationError as e:
                raise ValidationError(f"Chunk {chunk.id}: {str(e)}")

    def validate_metadata(self, metadata: Optional[Dict[str, Any]]) -> None:
        """Validate metadata.

        Args:
            metadata: Metadata to validate

        Raises:
            ValidationError: If validation fails
        """
        if not metadata:
            return

        if not isinstance(metadata, dict):
            raise ValidationError("Metadata must be a dictionary")
