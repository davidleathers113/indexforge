"""Embedding validation implementation.

This module provides validation strategies for embedding operations using
the core validation framework.
"""

from dataclasses import dataclass

from src.core.models.chunks import Chunk
from src.core.validation import (
    CompositeValidator,
    ContentValidationParams,
    ContentValidator,
    ValidationStrategy,
)
from src.core.validation.utils import validate_type


@dataclass
class EmbeddingValidationParams:
    """Parameters for embedding validation."""

    min_text_length: int = 10
    max_text_length: int = 1000000
    min_words: int = 3
    required_metadata_fields: set[str] | None = None
    optional_metadata_fields: set[str] | None = None


class EmbeddingValidator(ValidationStrategy[Chunk, EmbeddingValidationParams]):
    """Validates chunks for embedding generation."""

    def __init__(self) -> None:
        """Initialize the embedding validator."""
        super().__init__()
        self._content_validator = ContentValidator()

    def validate(self, chunk: Chunk, parameters: EmbeddingValidationParams) -> bool:
        """Validate chunk for embedding.

        Args:
            chunk: Chunk to validate
            parameters: Validation parameters

        Returns:
            True if validation passes
        """
        # Type validation
        self._errors.extend(validate_type(chunk, Chunk, "chunk"))
        if self._errors:
            return False

        # Content validation
        content_params = ContentValidationParams(
            min_length=parameters.min_text_length,
            max_length=parameters.max_text_length,
            min_words=parameters.min_words,
            required_fields=parameters.required_metadata_fields,
            optional_fields=parameters.optional_metadata_fields,
        )

        if not self._content_validator.validate(chunk, content_params):
            self._errors.extend(self._content_validator.errors)

        return not bool(self._errors)


def create_embedding_validator(
    min_text_length: int = 10,
    max_text_length: int = 1000000,
    min_words: int = 3,
    required_metadata_fields: set[str] | None = None,
    optional_metadata_fields: set[str] | None = None,
) -> CompositeValidator[Chunk]:
    """Create a configured embedding validator.

    Args:
        min_text_length: Minimum text length
        max_text_length: Maximum text length
        min_words: Minimum word count
        required_metadata_fields: Required metadata fields
        optional_metadata_fields: Optional metadata fields

    Returns:
        Configured composite validator
    """
    validator = EmbeddingValidator()
    validator.validate(
        Chunk(""),  # Dummy chunk for initialization
        EmbeddingValidationParams(
            min_text_length=min_text_length,
            max_text_length=max_text_length,
            min_words=min_words,
            required_metadata_fields=required_metadata_fields,
            optional_metadata_fields=optional_metadata_fields,
        ),
    )
    return CompositeValidator([validator])
