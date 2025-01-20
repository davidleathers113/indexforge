"""Processing validation implementation.

This module provides validation strategies for text processing operations
using the core validation framework.
"""

from dataclasses import dataclass
from typing import Optional

from src.core.models.chunks import Chunk
from src.core.validation import (
    BatchValidationParams,
    BatchValidator,
    CompositeValidator,
    ContentValidationParams,
    ContentValidator,
    ValidationStrategy,
)
from src.core.validation.utils import validate_metadata_structure, validate_type


@dataclass
class ProcessingValidationParams:
    """Parameters for processing validation."""

    min_text_length: int = 10
    max_text_length: int = 1000000
    min_words: int = 3
    max_batch_size: int = 1000
    max_memory_mb: int = 1024
    required_metadata_fields: Optional[set[str]] = None
    optional_metadata_fields: Optional[set[str]] = None


class ProcessingValidator(ValidationStrategy[Chunk, ProcessingValidationParams]):
    """Validates chunks for text processing."""

    def __init__(self) -> None:
        """Initialize the processing validator."""
        super().__init__()
        self._content_validator = ContentValidator()
        self._batch_validator = BatchValidator()

    def validate(self, chunk: Chunk, parameters: ProcessingValidationParams) -> list[str]:
        """Validate chunk for processing.

        Args:
            chunk: Chunk to validate
            parameters: Validation parameters

        Returns:
            List of validation error messages
        """
        errors = []

        # Type validation
        type_errors = validate_type(chunk, Chunk)
        if type_errors:
            errors.extend(type_errors)
            return errors

        # Content validation
        content_params = ContentValidationParams(
            min_length=parameters.min_text_length,
            max_length=parameters.max_text_length,
            min_words=parameters.min_words,
        )
        content_errors = self._content_validator.validate(chunk.content, content_params)
        errors.extend(content_errors)

        # Metadata validation
        if parameters.required_metadata_fields or parameters.optional_metadata_fields:
            metadata_errors = validate_metadata_structure(
                chunk.metadata,
                required_fields=parameters.required_metadata_fields,
                optional_fields=parameters.optional_metadata_fields,
            )
            errors.extend(metadata_errors)

        return errors

    def validate_batch(
        self, chunks: list[Chunk], parameters: ProcessingValidationParams
    ) -> list[str]:
        """Validate a batch of chunks.

        Args:
            chunks: Chunks to validate
            parameters: Validation parameters

        Returns:
            List of validation error messages
        """
        errors = []

        # Batch size validation
        batch_params = BatchValidationParams(
            max_batch_size=parameters.max_batch_size,
            max_memory_mb=parameters.max_memory_mb,
        )
        batch_errors = self._batch_validator.validate(chunks, batch_params)
        errors.extend(batch_errors)

        # Individual chunk validation
        for i, chunk in enumerate(chunks):
            chunk_errors = self.validate(chunk, parameters)
            if chunk_errors:
                errors.extend([f"Chunk {i}: {error}" for error in chunk_errors])

        return errors


def create_processing_validator(
    min_text_length: int = 10,
    max_text_length: int = 1000000,
    min_words: int = 3,
    max_batch_size: int = 1000,
    max_memory_mb: int = 1024,
    required_metadata_fields: Optional[set[str]] = None,
    optional_metadata_fields: Optional[set[str]] = None,
) -> CompositeValidator[Chunk]:
    """Create a configured processing validator.

    Args:
        min_text_length: Minimum text length
        max_text_length: Maximum text length
        min_words: Minimum number of words
        max_batch_size: Maximum batch size
        max_memory_mb: Maximum memory usage in MB
        required_metadata_fields: Required metadata fields
        optional_metadata_fields: Optional metadata fields

    Returns:
        Configured composite validator
    """
    params = ProcessingValidationParams(
        min_text_length=min_text_length,
        max_text_length=max_text_length,
        min_words=min_words,
        max_batch_size=max_batch_size,
        max_memory_mb=max_memory_mb,
        required_metadata_fields=required_metadata_fields,
        optional_metadata_fields=optional_metadata_fields,
    )

    return CompositeValidator[Chunk]([ProcessingValidator()], params)
