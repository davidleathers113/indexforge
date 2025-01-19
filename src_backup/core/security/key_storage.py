"""Secure key storage for IndexForge encryption keys.

This module provides secure storage functionality for encryption keys including:
- Secure file-based key storage with encryption
- Key metadata persistence
- Atomic file operations for consistency
- Key backup and recovery
"""

from datetime import datetime
import os
from pathlib import Path
from typing import Protocol
from uuid import UUID

from cryptography.fernet import Fernet
from pydantic import BaseModel, SecretStr

from src.core.errors import SecurityError
from src.core.security.encryption import EncryptionKey, KeyStatus


class KeyStorageError(SecurityError):
    """Base class for key storage errors."""


class KeyStorageConfig(BaseModel):
    """Configuration for key storage."""

    storage_dir: Path
    backup_dir: Path | None = None
    storage_key: SecretStr  # Used to encrypt keys at rest
    max_backup_count: int = 3
    enable_atomic_writes: bool = True


class KeyStorageProtocol(Protocol):
    """Protocol defining key storage interface."""

    async def store_key(self, key: EncryptionKey) -> None:
        """Store encryption key securely."""
        ...

    async def load_keys(self) -> dict[UUID, EncryptionKey]:
        """Load all stored encryption keys."""
        ...

    async def update_key_status(self, key_id: UUID, status: KeyStatus) -> None:
        """Update status of stored key."""
        ...

    async def delete_key(self, key_id: UUID) -> None:
        """Securely delete key from storage."""
        ...


class FileKeyStorage:
    """File-based secure key storage implementation."""

    def __init__(self, config: KeyStorageConfig):
        """Initialize file key storage.

        Args:
            config: Key storage configuration
        """
        self.config = config
        self._fernet = Fernet(config.storage_key.get_secret_value().encode())
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure storage directories exist with correct permissions."""
        self.config.storage_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.config.backup_dir:
            self.config.backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    def _get_key_path(self, key_id: UUID) -> Path:
        """Get path for key file."""
        return self.config.storage_dir / f"{key_id}.key"

    def _get_backup_path(self, key_id: UUID, timestamp: datetime) -> Path:
        """Get path for key backup file."""
        if not self.config.backup_dir:
            raise KeyStorageError("Backup directory not configured")
        return self.config.backup_dir / f"{key_id}_{timestamp.isoformat()}.key"

    async def _write_key_file(self, path: Path, key: EncryptionKey) -> None:
        """Write key to file securely.

        Args:
            path: Path to write key to
            key: Key to write
        """
        # Serialize key data
        key_data = key.json()

        # Encrypt serialized data
        encrypted_data = self._fernet.encrypt(key_data.encode())

        if self.config.enable_atomic_writes:
            # Write to temporary file first
            temp_path = path.with_suffix(".tmp")
            temp_path.write_bytes(encrypted_data)
            # Atomic rename
            temp_path.replace(path)
        else:
            # Direct write
            path.write_bytes(encrypted_data)

    async def _read_key_file(self, path: Path) -> EncryptionKey:
        """Read key from file securely.

        Args:
            path: Path to read key from

        Returns:
            Decrypted encryption key
        """
        # Read encrypted data
        encrypted_data = path.read_bytes()

        # Decrypt data
        key_data = self._fernet.decrypt(encrypted_data)

        # Deserialize key
        return EncryptionKey.parse_raw(key_data)

    async def store_key(self, key: EncryptionKey) -> None:
        """Store encryption key securely.

        Args:
            key: Key to store
        """
        key_path = self._get_key_path(key.id)

        # Create backup if key exists
        if key_path.exists() and self.config.backup_dir:
            backup_path = self._get_backup_path(key.id, datetime.utcnow())
            await self._write_key_file(backup_path, key)

            # Remove old backups if exceeding max count
            backups = sorted(self.config.backup_dir.glob(f"{key.id}_*.key"))
            while len(backups) > self.config.max_backup_count:
                backups[0].unlink()
                backups = backups[1:]

        # Store key
        await self._write_key_file(key_path, key)

    async def load_keys(self) -> dict[UUID, EncryptionKey]:
        """Load all stored encryption keys.

        Returns:
            Dictionary mapping key IDs to encryption keys
        """
        keys = {}
        for key_file in self.config.storage_dir.glob("*.key"):
            try:
                key = await self._read_key_file(key_file)
                keys[key.id] = key
            except Exception as e:
                # Log error but continue loading other keys
                print(f"Error loading key {key_file}: {e}")
        return keys

    async def update_key_status(self, key_id: UUID, status: KeyStatus) -> None:
        """Update status of stored key.

        Args:
            key_id: ID of key to update
            status: New key status
        """
        key_path = self._get_key_path(key_id)
        if not key_path.exists():
            raise KeyStorageError(f"Key {key_id} not found")

        # Read existing key
        key = await self._read_key_file(key_path)

        # Update status
        key.status = status

        # Store updated key
        await self.store_key(key)

    async def delete_key(self, key_id: UUID) -> None:
        """Securely delete key from storage.

        Args:
            key_id: ID of key to delete
        """
        key_path = self._get_key_path(key_id)
        if not key_path.exists():
            raise KeyStorageError(f"Key {key_id} not found")

        # Securely overwrite file before deletion
        with open(key_path, "wb") as f:
            # Write random data
            f.write(os.urandom(1024))
            f.flush()
            os.fsync(f.fileno())

        # Delete file
        key_path.unlink()

        # Delete backups if they exist
        if self.config.backup_dir:
            for backup in self.config.backup_dir.glob(f"{key_id}_*.key"):
                backup.unlink()
