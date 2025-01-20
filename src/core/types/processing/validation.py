"""Validation protocols for processing operations.

This module defines the protocols for validating document chunks and other
processing-related data structures.

Key Features:
    - Chunk validation protocols
    - Validation error handling
    - Type-safe validation operations
"""

from typing import Protocol

from src.core.models.chunks import Chunk


class ChunkValidator(Protocol):
    """Protocol for chunk validation operations."""

    def validate_chunk(self, chunk: Chunk) -> list[str]:
        """Validate a single chunk.

        Args:
            chunk (Chunk): Chunk to validate

        Returns:
            List[str]: List of validation error messages, empty if valid

        Raises:
            ValueError: If chunk is malformed
            TypeError: If chunk is not of correct type
        """
        ...

    def validate_chunks(self, chunks: list[Chunk]) -> list[str]:
        """Validate multiple chunks.

        Args:
            chunks (List[Chunk]): Chunks to validate

        Returns:
            List[str]: List of validation error messages, empty if all valid

        Raises:
            ValueError: If any chunk is malformed
            TypeError: If any chunk is not of correct type
        """
        ...
