"""Memory storage exceptions.

This module defines custom exceptions for memory storage operations,
providing specific error types for different failure scenarios.

Key Features:
    - Memory limit errors
    - Concurrency errors
    - Validation errors
    - Clear error hierarchies
"""

from __future__ import annotations

from src.core.types.storage import StorageError


class MemoryStorageError(StorageError):
    """Base exception for memory storage errors."""


class MemoryLimitExceededError(MemoryStorageError):
    """Raised when memory storage limit is exceeded."""


class ConcurrentModificationError(MemoryStorageError):
    """Raised when concurrent modification is detected."""


class ValidationError(MemoryStorageError):
    """Raised when data validation fails."""

    def __init__(self, message: str, data_type: type, actual_type: type) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            data_type: Expected data type
            actual_type: Actual data type received
        """
        super().__init__(f"{message} (expected: {data_type.__name__}, got: {actual_type.__name__})")
        self.data_type = data_type
        self.actual_type = actual_type
