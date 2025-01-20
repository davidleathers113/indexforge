"""Storage strategy protocols.

This module defines the core protocols for storage operations and serialization.
It provides interfaces that ensure consistent behavior across different storage
backends and serialization methods.
"""

from pathlib import Path
from typing import Protocol, TypeVar

T = TypeVar("T")


class StorageStrategy(Protocol[T]):
    """Protocol defining the interface for storage operations.

    This protocol establishes the contract for implementing storage backends,
    ensuring consistent operations across different storage implementations.
    """

    @property
    def storage_path(self) -> Path:
        """Get the storage path.

        Returns:
            Path: The path where data is stored
        """
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
    """Protocol for data serialization.

    This protocol defines the interface for serializing and deserializing
    data, allowing for different serialization methods to be used with
    storage implementations.
    """

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
