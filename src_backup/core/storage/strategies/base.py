"""Storage strategy protocols and base classes.

This module defines the core interfaces and base classes for storage implementations.
It provides protocols for storage operations and error handling, ensuring consistent
behavior across different storage backends.

Key Features:
    - Type-safe storage operations
    - Error handling protocols
    - Path management
    - Atomic operations
    - Serialization interfaces
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from pathlib import Path
from typing import Generic, Protocol, TypeVar

from src.core.models.documents import Document


logger = logging.getLogger(__name__)

T = TypeVar("T")
D = TypeVar("D", bound=Document)


class StorageError(Exception):
    """Base exception for storage-related errors."""


class DataNotFoundError(StorageError):
    """Raised when requested data is not found."""


class DataCorruptionError(StorageError):
    """Raised when data integrity is compromised."""


class StorageStrategy(Protocol[T]):
    """Protocol defining the interface for storage operations."""

    @property
    def storage_path(self) -> Path:
        """Get the storage path."""
        ...

    def save(self, key: str, data: T) -> None:
        """Save data to storage.

        Args:
            key: Unique identifier for the data
            data: Data to store

        Raises:
            StorageError: If save operation fails
        """
        ...

    def load(self, key: str) -> T:
        """Load data from storage.

        Args:
            key: Unique identifier for the data

        Returns:
            The loaded data

        Raises:
            DataNotFoundError: If data not found
            DataCorruptionError: If data is corrupted
            StorageError: If load operation fails
        """
        ...

    def delete(self, key: str) -> None:
        """Delete data from storage.

        Args:
            key: Unique identifier for the data

        Raises:
            DataNotFoundError: If data not found
            StorageError: If delete operation fails
        """
        ...

    def exists(self, key: str) -> bool:
        """Check if data exists in storage.

        Args:
            key: Unique identifier for the data

        Returns:
            True if data exists, False otherwise
        """
        ...


class SerializationStrategy(Protocol[T]):
    """Protocol for data serialization."""

    def serialize(self, data: T) -> bytes:
        """Serialize data to bytes.

        Args:
            data: Data to serialize

        Returns:
            Serialized data as bytes

        Raises:
            ValueError: If data cannot be serialized
        """
        ...

    def deserialize(self, data: bytes) -> T:
        """Deserialize data from bytes.

        Args:
            data: Serialized data

        Returns:
            Deserialized data

        Raises:
            ValueError: If data cannot be deserialized
            DataCorruptionError: If data is corrupted
        """
        ...


class BaseStorage(ABC, Generic[T]):
    """Abstract base class for storage implementations."""

    def __init__(
        self,
        storage_path: Path,
        serialization: SerializationStrategy[T],
    ) -> None:
        """Initialize storage.

        Args:
            storage_path: Path to storage directory
            serialization: Strategy for data serialization
        """
        self.storage_path = storage_path
        self._serialization = serialization
        self._ensure_storage_path()

    def _ensure_storage_path(self) -> None:
        """Ensure storage path exists."""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("Failed to create storage directory: %s", e)
            raise StorageError(f"Storage initialization failed: {e}") from e

    @abstractmethod
    def _get_path(self, key: str) -> Path:
        """Get path for a specific key.

        Args:
            key: Data identifier

        Returns:
            Path to the data
        """
        ...

    def save(self, key: str, data: T) -> None:
        """Save data to storage with atomic operations."""
        path = self._get_path(key)
        temp_path = path.with_suffix(".tmp")

        try:
            # Serialize and write to temporary file
            serialized = self._serialization.serialize(data)
            temp_path.write_bytes(serialized)

            # Atomic rename
            temp_path.replace(path)

        except Exception as e:
            logger.error("Failed to save data: %s", e)
            if temp_path.exists():
                temp_path.unlink()
            raise StorageError(f"Save operation failed: {e}") from e

    def load(self, key: str) -> T:
        """Load data from storage."""
        path = self._get_path(key)

        if not path.exists():
            raise DataNotFoundError(f"Data not found for key: {key}")

        try:
            data = path.read_bytes()
            return self._serialization.deserialize(data)
        except ValueError as e:
            raise DataCorruptionError(f"Data corruption detected: {e}") from e
        except Exception as e:
            logger.error("Failed to load data: %s", e)
            raise StorageError(f"Load operation failed: {e}") from e

    def delete(self, key: str) -> None:
        """Delete data from storage."""
        path = self._get_path(key)

        if not path.exists():
            raise DataNotFoundError(f"Data not found for key: {key}")

        try:
            path.unlink()
        except Exception as e:
            logger.error("Failed to delete data: %s", e)
            raise StorageError(f"Delete operation failed: {e}") from e

    def exists(self, key: str) -> bool:
        """Check if data exists in storage."""
        return self._get_path(key).exists()
