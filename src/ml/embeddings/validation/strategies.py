"""Validation strategies for embedding chunks.

This module provides various validation strategies for ensuring chunks meet
the requirements for embedding generation.
"""

import re
from abc import ABC, abstractmethod
from typing import List, Optional, Pattern

from src.core import Chunk


class ValidationStrategy(ABC):
    """Base class for chunk validation strategies."""

    @abstractmethod
    def validate(self, chunk: Chunk) -> List[str]:
        """Validate a chunk using this strategy.

        Args:
            chunk: The chunk to validate

        Returns:
            List of validation error messages, empty if valid

        Raises:
            TypeError: If chunk is not of correct type
        """
        pass


class BasicValidator(ValidationStrategy):
    """Basic chunk validation strategy.

    Validates fundamental chunk properties like existence and type.
    """

    def validate(self, chunk: Chunk) -> List[str]:
        """Validate basic chunk properties.

        Args:
            chunk: The chunk to validate

        Returns:
            List of validation error messages
        """
        errors: List[str] = []
        if not isinstance(chunk, Chunk):
            raise TypeError("Input must be a Chunk instance")
        if not chunk.content:
            errors.append("Chunk content is empty")
        return errors


class SemanticValidator(ValidationStrategy):
    """Semantic validation strategy for chunks.

    Validates semantic properties like content length, word count,
    and content quality.
    """

    def __init__(
        self,
        min_words: int = 3,
        min_size: int = 1024,  # 1KB
        max_size: int = 1024 * 1024,  # 1MB
    ) -> None:
        """Initialize the semantic validator.

        Args:
            min_words: Minimum number of words required
            min_size: Minimum content size in bytes
            max_size: Maximum content size in bytes
        """
        self.min_words = min_words
        self.min_size = min_size
        self.max_size = max_size

    def validate(self, chunk: Chunk) -> List[str]:
        """Validate semantic properties of the chunk.

        Args:
            chunk: The chunk to validate

        Returns:
            List of validation error messages
        """
        errors: List[str] = []

        if not chunk.content.strip():
            errors.append("Chunk content is empty or whitespace")

        word_count = len(chunk.content.split())
        if word_count < self.min_words:
            errors.append(f"Chunk contains fewer than {self.min_words} words")

        content_bytes = len(chunk.content.encode("utf-8"))
        if content_bytes < self.min_size:
            errors.append(
                f"Chunk size ({content_bytes} bytes) is below minimum {self.min_size} bytes"
            )
        if content_bytes > self.max_size:
            errors.append(
                f"Chunk size ({content_bytes} bytes) exceeds maximum {self.max_size} bytes"
            )

        return errors


class QualityValidator(ValidationStrategy):
    """Quality validation strategy for chunks.

    Validates content quality aspects like:
    - Minimum content entropy
    - Maximum repetition
    - Special character ratio
    - Valid character encoding
    """

    def __init__(
        self,
        max_repetition_ratio: float = 0.3,
        max_special_char_ratio: float = 0.1,
        excluded_patterns: Optional[List[Pattern[str]]] = None,
    ) -> None:
        """Initialize the quality validator.

        Args:
            max_repetition_ratio: Maximum allowed ratio of repeated content
            max_special_char_ratio: Maximum ratio of special characters
            excluded_patterns: Optional list of regex patterns to exclude
        """
        self.max_repetition_ratio = max_repetition_ratio
        self.max_special_char_ratio = max_special_char_ratio
        self.excluded_patterns = excluded_patterns or [
            re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"),  # Control chars
            re.compile(r"(.)\1{4,}"),  # Repeated chars
        ]

    def validate(self, chunk: Chunk) -> List[str]:
        """Validate quality aspects of the chunk content.

        Args:
            chunk: The chunk to validate

        Returns:
            List of validation error messages
        """
        errors: List[str] = []
        content = chunk.content

        # Check for excluded patterns
        for pattern in self.excluded_patterns:
            if pattern.search(content):
                errors.append(f"Content contains invalid pattern: {pattern.pattern}")

        # Check character ratios
        special_chars = sum(1 for c in content if not c.isalnum() and not c.isspace())
        special_ratio = special_chars / len(content) if content else 1.0
        if special_ratio > self.max_special_char_ratio:
            errors.append(
                f"Special character ratio ({special_ratio:.2f}) exceeds maximum "
                f"({self.max_special_char_ratio:.2f})"
            )

        # Check for repetitive content
        words = content.split()
        if words:
            unique_words = len(set(words))
            repetition_ratio = 1 - (unique_words / len(words))
            if repetition_ratio > self.max_repetition_ratio:
                errors.append(
                    f"Content repetition ratio ({repetition_ratio:.2f}) exceeds maximum "
                    f"({self.max_repetition_ratio:.2f})"
                )

        # Validate UTF-8 encoding
        try:
            content.encode("utf-8").decode("utf-8")
        except UnicodeError:
            errors.append("Content contains invalid UTF-8 characters")

        return errors
