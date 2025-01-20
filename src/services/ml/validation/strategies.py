"""Validation strategies for ML services.

This module provides validation strategies for different types of validation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from src.core.models.chunks import Chunk

from .parameters import BatchValidationParameters, ValidationParameters

T = TypeVar("T")


class ValidationStrategy(Generic[T], ABC):
    """Base validation strategy."""

    @abstractmethod
    def validate(self, value: T, parameters: Any) -> List[str]:
        """Validate a value.

        Args:
            value: Value to validate
            parameters: Validation parameters

        Returns:
            List of validation error messages
        """
        pass


class ContentValidationStrategy(ValidationStrategy[str]):
    """Validates text content."""

    def validate(self, content: str, parameters: ValidationParameters) -> List[str]:
        """Validate text content.

        Args:
            content: Text content to validate
            parameters: Validation parameters

        Returns:
            List of validation error messages
        """
        errors = []

        if not content:
            errors.append("Content cannot be empty")
            return errors

        if len(content) < parameters.min_text_length:
            errors.append(
                f"Content length {len(content)} is below minimum {parameters.min_text_length}"
            )

        if len(content) > parameters.max_text_length:
            errors.append(
                f"Content length {len(content)} exceeds maximum {parameters.max_text_length}"
            )

        word_count = len(content.split())
        if word_count < parameters.min_words:
            errors.append(f"Word count {word_count} is below minimum {parameters.min_words}")

        return errors


class BatchValidationStrategy(ValidationStrategy[List[Any]]):
    """Validates batch operations."""

    def validate(self, items: List[Any], parameters: BatchValidationParameters) -> List[str]:
        """Validate a batch of items.

        Args:
            items: Items to validate
            parameters: Batch validation parameters

        Returns:
            List of validation error messages
        """
        errors = []

        if not items:
            errors.append("Batch cannot be empty")
            return errors

        if len(items) > parameters.max_batch_size:
            errors.append(f"Batch size {len(items)} exceeds maximum {parameters.max_batch_size}")

        return errors


class MetadataValidationStrategy(ValidationStrategy[Dict[str, Any]]):
    """Validates metadata structure."""

    def validate(self, metadata: Dict[str, Any], parameters: ValidationParameters) -> List[str]:
        """Validate metadata.

        Args:
            metadata: Metadata to validate
            parameters: Validation parameters

        Returns:
            List of validation error messages
        """
        errors = []

        if parameters.required_metadata_fields:
            missing = parameters.required_metadata_fields - set(metadata.keys())
            if missing:
                errors.append(f"Missing required metadata fields: {missing}")

        if parameters.optional_metadata_fields:
            invalid = (
                set(metadata.keys())
                - (parameters.required_metadata_fields or set())
                - parameters.optional_metadata_fields
            )
            if invalid:
                errors.append(f"Invalid metadata fields: {invalid}")

        return errors


class ChunkValidationStrategy(ValidationStrategy[Chunk]):
    """Validates chunks using composite validation."""

    def __init__(self) -> None:
        """Initialize chunk validator."""
        self._content_validator = ContentValidationStrategy()
        self._metadata_validator = MetadataValidationStrategy()

    def validate(self, chunk: Chunk, parameters: ValidationParameters) -> List[str]:
        """Validate a chunk.

        Args:
            chunk: Chunk to validate
            parameters: Validation parameters

        Returns:
            List of validation error messages
        """
        errors = []

        # Validate content
        content_errors = self._content_validator.validate(chunk.content, parameters)
        errors.extend(content_errors)

        # Validate metadata if present
        if chunk.metadata:
            metadata_errors = self._metadata_validator.validate(chunk.metadata, parameters)
            errors.extend(metadata_errors)

        return errors
