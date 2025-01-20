"""Service-specific validators.

This module provides validator creation functions for specific services.
"""

from typing import Optional

from .manager import ValidationManager
from .parameters import (
    BatchValidationParameters,
    EmbeddingParameters,
    ProcessingParameters,
    ValidationParameters,
)


def create_processing_validator(
    min_text_length: int = 10,
    max_text_length: int = 1000000,
    min_words: int = 3,
    max_batch_size: int = 1000,
    max_memory_mb: int = 1024,
    required_metadata_fields: Optional[set[str]] = None,
    optional_metadata_fields: Optional[set[str]] = None,
) -> ValidationManager:
    """Create a configured validator for processing service.

    Args:
        min_text_length: Minimum text length
        max_text_length: Maximum text length
        min_words: Minimum number of words
        max_batch_size: Maximum batch size
        max_memory_mb: Maximum memory usage in MB
        required_metadata_fields: Required metadata fields
        optional_metadata_fields: Optional metadata fields

    Returns:
        Configured validation manager
    """
    validation_params = ValidationParameters(
        min_text_length=min_text_length,
        max_text_length=max_text_length,
        min_words=min_words,
        required_metadata_fields=required_metadata_fields,
        optional_metadata_fields=optional_metadata_fields,
    )

    batch_params = BatchValidationParameters(
        max_batch_size=max_batch_size,
        max_memory_mb=max_memory_mb,
    )

    return ValidationManager(validation_params, batch_params)


def create_embedding_validator(
    min_text_length: int = 10,
    max_text_length: int = 1000,
    min_words: int = 3,
    max_batch_size: int = 32,
    required_metadata_fields: Optional[set[str]] = None,
    optional_metadata_fields: Optional[set[str]] = None,
) -> ValidationManager:
    """Create a configured validator for embedding service.

    Args:
        min_text_length: Minimum text length
        max_text_length: Maximum text length
        min_words: Minimum number of words
        max_batch_size: Maximum batch size
        required_metadata_fields: Required metadata fields
        optional_metadata_fields: Optional metadata fields

    Returns:
        Configured validation manager
    """
    validation_params = ValidationParameters(
        min_text_length=min_text_length,
        max_text_length=max_text_length,
        min_words=min_words,
        required_metadata_fields=required_metadata_fields,
        optional_metadata_fields=optional_metadata_fields,
    )

    batch_params = BatchValidationParameters(
        max_batch_size=max_batch_size,
    )

    return ValidationManager(validation_params, batch_params)
