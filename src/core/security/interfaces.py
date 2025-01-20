"""Security service interfaces.

This module defines the core interfaces for security-related services,
establishing clear boundaries and preventing circular dependencies.
"""

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


@runtime_checkable
class KeyStorageProtocol(Protocol):
    """Protocol defining the interface for key storage operations."""

    @abstractmethod
    async def store_key(self, key_id: str, key_data: bytes) -> None:
        """Store an encryption key."""
        ...

    @abstractmethod
    async def retrieve_key(self, key_id: str) -> bytes:
        """Retrieve an encryption key."""
        ...

    @abstractmethod
    async def delete_key(self, key_id: str) -> None:
        """Delete an encryption key."""
        ...

    @abstractmethod
    async def rotate_key(self, key_id: str) -> bytes:
        """Rotate an encryption key."""
        ...


@runtime_checkable
class EncryptionProtocol(Protocol):
    """Protocol defining the interface for encryption operations."""

    @abstractmethod
    async def encrypt(self, data: bytes, key_id: str = None) -> tuple[bytes, str]:
        """Encrypt data using the specified or default key."""
        ...

    @abstractmethod
    async def decrypt(self, encrypted_data: bytes, key_id: str) -> bytes:
        """Decrypt data using the specified key."""
        ...

    @abstractmethod
    async def rotate_encryption(
        self, data: bytes, old_key_id: str, new_key_id: str
    ) -> tuple[bytes, str]:
        """Re-encrypt data using a new key."""
        ...


class SecurityServiceBase(ABC):
    """Base class for security services with common functionality."""

    def __init__(self, key_storage: KeyStorageProtocol = None):
        """Initialize the security service."""
        self._key_storage = key_storage

    @property
    def key_storage(self) -> KeyStorageProtocol:
        """Get the key storage implementation."""
        if self._key_storage is None:
            raise ValueError("Key storage not initialized")
        return self._key_storage

    @key_storage.setter
    def key_storage(self, storage: KeyStorageProtocol) -> None:
        """Set the key storage implementation."""
        if not isinstance(storage, KeyStorageProtocol):
            raise TypeError("Storage must implement KeyStorageProtocol")
        self._key_storage = storage
