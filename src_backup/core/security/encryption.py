"""Encryption infrastructure for IndexForge.

This module provides encryption functionality including:
- Data encryption/decryption using AES-256-GCM
- Key management with key rotation
- Secure key storage
- Encrypted data persistence
"""

import base64
from datetime import datetime, timedelta
from enum import Enum
import os
from uuid import UUID, uuid4

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import aead
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pydantic import BaseModel, SecretStr

from src.core.errors import SecurityError
from src.core.security.key_storage import FileKeyStorage, KeyStorageConfig


class EncryptionError(SecurityError):
    """Base class for encryption errors."""


class KeyGenerationError(EncryptionError):
    """Raised when key generation fails."""

    def __init__(self, message: str = "Failed to generate encryption key"):
        super().__init__(message)


class EncryptionKeyNotFoundError(EncryptionError):
    """Raised when encryption key is not found."""

    def __init__(self, message: str = "Encryption key not found"):
        super().__init__(message)


class DecryptionError(EncryptionError):
    """Raised when decryption fails."""

    def __init__(self, message: str = "Failed to decrypt data"):
        super().__init__(message)


class KeyStatus(str, Enum):
    """Status of encryption keys."""

    ACTIVE = "active"  # Currently used for encryption
    ENABLED = "enabled"  # Can be used for decryption
    DISABLED = "disabled"  # Cannot be used, pending deletion
    DELETED = "deleted"  # Marked for secure deletion


class EncryptionKey(BaseModel):
    """Encryption key with metadata."""

    id: UUID
    key_data: SecretStr
    created_at: datetime
    expires_at: datetime | None
    status: KeyStatus = KeyStatus.ACTIVE
    version: int
    key_type: str = "AES256-GCM"


class EncryptedData(BaseModel):
    """Container for encrypted data."""

    key_id: UUID
    nonce: bytes
    ciphertext: bytes
    tag: bytes
    version: int
    created_at: datetime


class EncryptionConfig(BaseModel):
    """Configuration for encryption service."""

    master_key: SecretStr
    key_rotation_days: int = 30
    min_key_retention_days: int = 90
    pbkdf2_iterations: int = 100000
    storage: KeyStorageConfig | None = None


class EncryptionManager:
    """Manages encryption operations and key lifecycle."""

    def __init__(self, config: EncryptionConfig):
        """Initialize encryption manager.

        Args:
            config: Encryption configuration
        """
        self.config = config
        self._keys: dict[UUID, EncryptionKey] = {}
        self._active_key: UUID | None = None
        self._key_version = 0
        self._storage: FileKeyStorage | None = None

        # Initialize storage if configured
        if self.config.storage:
            self._storage = FileKeyStorage(self.config.storage)

    async def _init_storage(self) -> None:
        """Initialize key storage and load existing keys."""
        if not self._storage:
            return

        # Load existing keys
        stored_keys = await self._storage.load_keys()
        self._keys.update(stored_keys)

        # Find active key and highest version
        for key in stored_keys.values():
            if key.status == KeyStatus.ACTIVE:
                self._active_key = key.id
            self._key_version = max(self._key_version, key.version)

    def _derive_key(self, master_key: str, salt: bytes) -> bytes:
        """Derive encryption key from master key.

        Args:
            master_key: Master key to derive from
            salt: Salt for key derivation

        Returns:
            Derived key bytes

        Raises:
            KeyGenerationError: If key derivation fails
        """
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  # 256 bits for AES-256
                salt=salt,
                iterations=self.config.pbkdf2_iterations,
            )
            return kdf.derive(master_key.encode())
        except Exception as e:
            raise KeyGenerationError(f"Key derivation failed: {e!s}")

    async def create_key(self) -> EncryptionKey:
        """Create new encryption key.

        Returns:
            Created encryption key

        Raises:
            KeyGenerationError: If key generation fails
        """
        try:
            # Generate salt and derive key
            salt = os.urandom(16)
            key_bytes = self._derive_key(
                self.config.master_key.get_secret_value(),
                salt,
            )

            # Create key with metadata
            self._key_version += 1
            key = EncryptionKey(
                id=uuid4(),
                key_data=SecretStr(base64.b64encode(key_bytes).decode()),
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=self.config.key_rotation_days),
                version=self._key_version,
            )

            # Store key in memory
            self._keys[key.id] = key
            self._active_key = key.id

            # Store key persistently if storage configured
            if self._storage:
                await self._storage.store_key(key)

            return key
        except Exception as e:
            raise KeyGenerationError(f"Failed to create key: {e!s}")

    async def rotate_keys(self) -> None:
        """Rotate encryption keys.

        Creates new active key and updates status of old keys.
        """
        # Create new active key
        new_key = await self.create_key()

        # Update status of old keys
        now = datetime.utcnow()
        retention_limit = now - timedelta(days=self.config.min_key_retention_days)

        for key in self._keys.values():
            if key.id == new_key.id:
                continue

            old_status = key.status
            if key.status == KeyStatus.ACTIVE:
                key.status = KeyStatus.ENABLED
            elif key.status == KeyStatus.ENABLED and key.created_at < retention_limit:
                key.status = KeyStatus.DISABLED
            elif key.status == KeyStatus.DISABLED and key.created_at < retention_limit:
                key.status = KeyStatus.DELETED

            # Update key status in storage if changed
            if self._storage and old_status != key.status:
                await self._storage.update_key_status(key.id, key.status)

            # Delete key if marked for deletion
            if key.status == KeyStatus.DELETED and self._storage:
                await self._storage.delete_key(key.id)
                del self._keys[key.id]

    async def get_key(self, key_id: UUID) -> EncryptionKey:
        """Get encryption key by ID.

        Args:
            key_id: ID of key to get

        Returns:
            Encryption key

        Raises:
            EncryptionKeyNotFoundError: If key not found
        """
        key = self._keys.get(key_id)
        if not key or key.status == KeyStatus.DELETED:
            raise EncryptionKeyNotFoundError(f"Key {key_id} not found or deleted")
        return key

    async def encrypt(self, data: bytes) -> EncryptedData:
        """Encrypt data using active key.

        Args:
            data: Data to encrypt

        Returns:
            Encrypted data container

        Raises:
            EncryptionError: If encryption fails
        """
        if not self._active_key:
            await self.create_key()

        try:
            key = await self.get_key(self._active_key)
            key_bytes = base64.b64decode(key.key_data.get_secret_value())

            # Generate nonce
            nonce = os.urandom(12)  # 96 bits for GCM

            # Create cipher
            cipher = aead.AESGCM(key_bytes)

            # Encrypt data
            ciphertext = cipher.encrypt(
                nonce,
                data,
                None,  # No associated data
            )

            # Split ciphertext and tag
            tag = ciphertext[-16:]  # Last 16 bytes
            ciphertext = ciphertext[:-16]  # Everything except last 16 bytes

            return EncryptedData(
                key_id=key.id,
                nonce=nonce,
                ciphertext=ciphertext,
                tag=tag,
                version=key.version,
                created_at=datetime.utcnow(),
            )
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e!s}")

    async def decrypt(self, encrypted_data: EncryptedData) -> bytes:
        """Decrypt encrypted data.

        Args:
            encrypted_data: Encrypted data container

        Returns:
            Decrypted data

        Raises:
            DecryptionError: If decryption fails
        """
        try:
            key = await self.get_key(encrypted_data.key_id)
            if key.status == KeyStatus.DISABLED:
                raise DecryptionError("Key is disabled")

            key_bytes = base64.b64decode(key.key_data.get_secret_value())

            # Create cipher
            cipher = aead.AESGCM(key_bytes)

            # Combine ciphertext and tag
            ciphertext_with_tag = encrypted_data.ciphertext + encrypted_data.tag

            # Decrypt data
            return cipher.decrypt(
                encrypted_data.nonce,
                ciphertext_with_tag,
                None,  # No associated data
            )
        except EncryptionKeyNotFoundError:
            raise DecryptionError("Decryption key not found")
        except Exception as e:
            raise DecryptionError(f"Decryption failed: {e!s}")
