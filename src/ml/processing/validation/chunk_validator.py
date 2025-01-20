"""Validation utilities for processing chunks."""

from src.core.types.processing import ChunkValidator as ChunkValidatorProtocol
from src.ml.processing.models.chunks import Chunk
from src.ml.processing.validation.validators import (
    BatchValidator,
    ContentQualityValidator,
    LanguageValidator,
    SizeValidator,
    ValidatorBuilder,
)


class ChunkValidator(ChunkValidatorProtocol):
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
        supported_languages: set[str] | None = None,
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

    def validate_chunk(self, chunk: Chunk) -> list[str]:
        """Validate a chunk before processing.

        Args:
            chunk: Chunk to validate

        Returns:
            List of validation error messages, empty if valid

        Raises:
            TypeError: If chunk is not of correct type
        """
        if not isinstance(chunk, Chunk):
            raise TypeError("Input must be a Chunk instance")

        return self._validator.validate(chunk, None)

    def validate_chunks(self, chunks: list[Chunk]) -> list[str]:
        """Validate a batch of chunks.

        Args:
            chunks: List of chunks to validate

        Returns:
            List of validation error messages, empty if all valid

        Raises:
            TypeError: If chunks is not a list or contains invalid types
            ValueError: If batch size exceeds maximum
        """
        if not isinstance(chunks, list):
            raise TypeError("Input must be a list of Chunk instances")

        all_errors = []
        for i, chunk in enumerate(chunks):
            try:
                errors = self.validate_chunk(chunk)
                if errors:
                    all_errors.extend([f"Chunk {i}: {error}" for error in errors])
            except TypeError as e:
                all_errors.append(f"Chunk {i}: {str(e)}")

        return all_errors
