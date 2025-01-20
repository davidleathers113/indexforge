"""Secure key storage for IndexForge encryption keys.

This module provides secure storage functionality for encryption keys including:
- Secure file-based key storage with encryption
- Key metadata persistence
- Atomic file operations for consistency
- Key backup and recovery
"""

import os
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet
from pydantic import BaseModel, SecretStr

from src.core.types.security import MINIMUM_KEY_LENGTH, SecurityError

from .interfaces import KeyStorageProtocol


class KeyStorageConfig(BaseModel):
    """Configuration for key storage."""

    storage_dir: Path
    backup_dir: Path | None = None
    storage_key: SecretStr  # Used to encrypt keys at rest
    max_backup_count: int = 3
    enable_atomic_writes: bool = True


class FileKeyStorage(KeyStorageProtocol):
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

    def _get_key_path(self, key_id: str) -> Path:
        """Get path for key file."""
        return self.config.storage_dir / f"{key_id}.key"

    def _get_backup_path(self, key_id: str, timestamp: datetime) -> Path:
        """Get path for key backup file."""
        if not self.config.backup_dir:
            raise SecurityError("Backup directory not configured")
        return self.config.backup_dir / f"{key_id}_{timestamp.isoformat()}.key"

    async def _write_key_file(self, path: Path, key_data: bytes) -> None:
        """Write key to file securely.

        Args:
            path: Path to write key to
            key_data: Key data to write
        """
        # Encrypt key data
        encrypted_data = self._fernet.encrypt(key_data)

        if self.config.enable_atomic_writes:
            # Write to temporary file first
            temp_path = path.with_suffix(".tmp")
            temp_path.write_bytes(encrypted_data)
            # Atomic rename
            temp_path.replace(path)
        else:
            # Direct write
            path.write_bytes(encrypted_data)

    async def _read_key_file(self, path: Path) -> bytes:
        """Read key from file securely.

        Args:
            path: Path to read key from

        Returns:
            Decrypted key data
        """
        # Read encrypted data
        encrypted_data = path.read_bytes()

        # Decrypt data
        return self._fernet.decrypt(encrypted_data)

    async def store_key(self, key_id: str, key_data: bytes) -> None:
        """Store encryption key securely.

        Args:
            key_id: ID of key to store
            key_data: Key data to store
        """
        if len(key_data) < MINIMUM_KEY_LENGTH:
            raise SecurityError(f"Key data must be at least {MINIMUM_KEY_LENGTH} bytes")

        key_path = self._get_key_path(key_id)

        # Create backup if key exists
        if key_path.exists() and self.config.backup_dir:
            backup_path = self._get_backup_path(key_id, datetime.utcnow())
            await self._write_key_file(backup_path, key_data)

            # Remove old backups if exceeding max count
            backups = sorted(self.config.backup_dir.glob(f"{key_id}_*.key"))
            while len(backups) > self.config.max_backup_count:
                backups[0].unlink()
                backups = backups[1:]

        # Store key
        await self._write_key_file(key_path, key_data)

    async def retrieve_key(self, key_id: str) -> bytes:
        """Retrieve encryption key.

        Args:
            key_id: ID of key to retrieve

        Returns:
            Key data

        Raises:
            SecurityError: If key not found
        """
        key_path = self._get_key_path(key_id)
        if not key_path.exists():
            raise SecurityError(f"Key {key_id} not found")

        return await self._read_key_file(key_path)

    async def delete_key(self, key_id: str) -> None:
        """Securely delete key from storage.

        Args:
            key_id: ID of key to delete

        Raises:
            SecurityError: If key not found
        """
        key_path = self._get_key_path(key_id)
        if not key_path.exists():
            raise SecurityError(f"Key {key_id} not found")

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

    async def rotate_key(self, key_id: str) -> bytes:
        """Rotate encryption key.

        Args:
            key_id: ID of key to rotate

        Returns:
            New key data

        Raises:
            SecurityError: If key not found
        """
        # Generate new key
        new_key_data = os.urandom(MINIMUM_KEY_LENGTH)

        # Store new key (this will automatically create a backup of the old key)
        await self.store_key(key_id, new_key_data)

        return new_key_data
