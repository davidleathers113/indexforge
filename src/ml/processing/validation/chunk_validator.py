"""Validation utilities for processing chunks."""

from typing import Dict, List, Optional, Set

from src.ml.processing.models.chunks import Chunk
from src.ml.processing.validation.validators import (
    BatchValidator,
    ContentQualityValidator,
    LanguageValidator,
    SizeValidator,
    ValidatorBuilder,
)


class ChunkValidator:
    """Validates chunks before processing.

    This class provides validation utilities for ensuring chunks
    meet the required criteria before processing.

    Attributes:
        max_chunk_size: Maximum allowed chunk size in characters
        min_chunk_size: Minimum allowed chunk size in characters
        max_batch_size: Maximum number of chunks in a batch
        supported_languages: Set of supported language codes
        min_content_density: Minimum ratio of meaningful content
    """

    def __init__(
        self,
        max_chunk_size: int = 10000,
        min_chunk_size: int = 50,
        max_batch_size: int = 1000,
        supported_languages: Optional[Set[str]] = None,
        min_content_density: float = 0.3,
    ):
        """Initialize the validator.

        Args:
            max_chunk_size: Maximum allowed chunk size
            min_chunk_size: Minimum allowed chunk size
            max_batch_size: Maximum batch size
            supported_languages: Set of supported language codes
            min_content_density: Minimum content density ratio
        """
        # Build validation chain
        self._validator = (
            ValidatorBuilder()
            .add_validator(SizeValidator(min_chunk_size, max_chunk_size))
            .add_validator(ContentQualityValidator(min_content_density))
            .add_validator(LanguageValidator(supported_languages))
            .add_validator(BatchValidator(max_batch_size))
            .build()
        )

    def validate(self, chunk: Chunk, metadata: Optional[Dict] = None) -> List[str]:
        """Validate a chunk before processing.

        Args:
            chunk: Chunk to validate
            metadata: Optional metadata to include in validation context

        Returns:
            List of validation error messages, empty if valid

        Raises:
            TypeError: If chunk is not of correct type
        """
        if not isinstance(chunk, Chunk):
            raise TypeError("Input must be a Chunk instance")

        return self._validator.validate(chunk, metadata)

    def validate_batch(
        self, chunks: List[Chunk], metadata: Optional[Dict] = None
    ) -> List[tuple[int, List[str]]]:
        """Validate a batch of chunks.

        Args:
            chunks: List of chunks to validate
            metadata: Optional metadata to include in validation context

        Returns:
            List of tuples containing (chunk_index, error_messages)

        Raises:
            TypeError: If chunks is not a list or contains invalid types
            ValidationError: If batch size exceeds maximum
        """
        if not isinstance(chunks, list):
            raise TypeError("Input must be a list of Chunk instances")

        validation_results = []
        for i, chunk in enumerate(chunks):
            try:
                # Add batch context to metadata
                batch_metadata = metadata.copy() if metadata else {}
                batch_metadata["batch"] = chunks

                errors = self.validate(chunk, batch_metadata)
                if errors:
                    validation_results.append((i, errors))
            except TypeError as e:
                validation_results.append((i, [str(e)]))

        return validation_results
