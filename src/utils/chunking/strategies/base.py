"""Base chunking strategy definitions.

This module defines the base interfaces and abstract classes for text chunking strategies.
"""

from abc import ABC, abstractmethod
from typing import Protocol


class ChunkValidator(Protocol):
    """Protocol for chunk validation."""

    def validate_chunk_size(self, size: int) -> None:
        """Validate chunk size."""
        ...

    def validate_overlap(self, overlap: int, chunk_size: int) -> None:
        """Validate overlap size."""
        ...


class ChunkingStrategy(ABC):
    """Base class for text chunking strategies."""

    def __init__(self, validator: ChunkValidator | None = None):
        """Initialize the chunking strategy.

        Args:
            validator: Optional validator for chunking parameters
        """
        self.validator = validator

    def validate_params(self, chunk_size: int, overlap: int) -> None:
        """Validate chunking parameters.

        Args:
            chunk_size: Size of each chunk
            overlap: Number of overlapping units between chunks

        Raises:
            ValueError: If parameters are invalid
        """
        if self.validator:
            self.validator.validate_chunk_size(chunk_size)
            self.validator.validate_overlap(overlap, chunk_size)

    @abstractmethod
    def chunk(self, text: str, chunk_size: int, overlap: int = 0) -> list[str]:
        """Split text into chunks.

        Args:
            text: Text to split into chunks
            chunk_size: Size of each chunk
            overlap: Number of overlapping units between chunks

        Returns:
            List of text chunks

        Raises:
            ValueError: If chunking parameters are invalid
        """
        pass
