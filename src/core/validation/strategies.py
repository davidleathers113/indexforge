"""Validation strategy framework.

This module provides common validation strategies that can be used across
different services and components.
"""

from dataclasses import dataclass
from typing import Any, TypeVar

from .base import ValidationStrategy
from .utils import validate_length, validate_metadata_structure, validate_range

T = TypeVar("T")


@dataclass
class ContentValidationParams:
    """Parameters for content validation."""

    min_length: int | None = None
    max_length: int | None = None
    min_words: int | None = None
    max_words: int | None = None
    required_fields: set[str] | None = None
    optional_fields: set[str] | None = None


class ContentValidator(ValidationStrategy[T, ContentValidationParams]):
    """Validates content structure and constraints."""

    def validate(self, value: T, parameters: ContentValidationParams) -> bool:
        """Validate content.

        Args:
            value: Content to validate
            parameters: Validation parameters

        Returns:
            True if validation passes
        """
        # Validate basic content constraints
        if hasattr(value, "content"):
            content = getattr(value, "content")
            self._errors.extend(
                validate_length(
                    content,
                    "content",
                    parameters.min_length,
                    parameters.max_length,
                )
            )

            if parameters.min_words or parameters.max_words:
                word_count = len(content.split())
                self._errors.extend(
                    validate_range(
                        word_count,
                        "word count",
                        parameters.min_words,
                        parameters.max_words,
                    )
                )

        # Validate required/optional fields
        if parameters.required_fields or parameters.optional_fields:
            if hasattr(value, "__dict__"):
                fields = value.__dict__
                self._errors.extend(
                    validate_metadata_structure(
                        fields,
                        parameters.required_fields,
                        parameters.optional_fields,
                    )
                )

        return not bool(self._errors)


@dataclass
class BatchValidationParams:
    """Parameters for batch validation."""

    min_batch_size: int | None = None
    max_batch_size: int | None = None
    require_uniform_type: bool = True
    max_memory_mb: int | None = None


class BatchValidator(ValidationStrategy[list[T], BatchValidationParams]):
    """Validates batch operations."""

    def validate(self, value: list[T], parameters: BatchValidationParams) -> bool:
        """Validate batch.

        Args:
            value: Batch to validate
            parameters: Validation parameters

        Returns:
            True if validation passes
        """
        # Validate batch size
        self._errors.extend(
            validate_length(
                value,
                "batch",
                parameters.min_batch_size,
                parameters.max_batch_size,
            )
        )

        # Validate uniform type if required
        if parameters.require_uniform_type and value:
            expected_type = type(value[0])
            for i, item in enumerate(value[1:], 1):
                if not isinstance(item, expected_type):
                    self._errors.append(
                        f"Item at index {i} has type {type(item)}, expected {expected_type}"
                    )

        # Validate memory usage if specified
        if parameters.max_memory_mb is not None:
            try:
                import sys

                memory_size = sum(sys.getsizeof(item) for item in value) / (1024 * 1024)
                if memory_size > parameters.max_memory_mb:
                    self._errors.append(
                        f"Batch memory size {memory_size:.1f}MB exceeds limit {parameters.max_memory_mb}MB"
                    )
            except Exception as e:
                self._errors.append(f"Failed to check memory usage: {e}")

        return not bool(self._errors)


@dataclass
class MetadataValidationParams:
    """Parameters for metadata validation."""

    required_fields: set[str] | None = None
    optional_fields: set[str] | None = None
    max_depth: int | None = None
    max_size_bytes: int | None = None


class MetadataValidator(ValidationStrategy[dict[str, Any], MetadataValidationParams]):
    """Validates metadata structure and constraints."""

    def validate(self, value: dict[str, Any], parameters: MetadataValidationParams) -> bool:
        """Validate metadata.

        Args:
            value: Metadata to validate
            parameters: Validation parameters

        Returns:
            True if validation passes
        """
        # Validate metadata structure
        self._errors.extend(
            validate_metadata_structure(
                value,
                parameters.required_fields,
                parameters.optional_fields,
                parameters.max_depth,
            )
        )

        # Validate size if specified
        if parameters.max_size_bytes is not None:
            try:
                import json
                import sys

                size = sys.getsizeof(json.dumps(value))
                if size > parameters.max_size_bytes:
                    self._errors.append(
                        f"Metadata size {size} bytes exceeds limit {parameters.max_size_bytes}"
                    )
            except Exception as e:
                self._errors.append(f"Failed to check metadata size: {e}")

        return not bool(self._errors)
