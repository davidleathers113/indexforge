"""Encryption infrastructure for IndexForge.

This module provides encryption functionality including:
- Data encryption/decryption using AES-256-GCM
- Key management with key rotation
- Secure key storage
- Encrypted data persistence
"""

import os
from typing import Optional
from uuid import uuid4

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import aead
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pydantic import BaseModel, SecretStr

from src.core.types.security import (
    DEFAULT_KEY_EXPIRY_DAYS,
    MINIMUM_KEY_LENGTH,
    EncryptionError,
    KeyNotFoundError,
    KeyRotationError,
)

from .interfaces import EncryptionProtocol, KeyStorageProtocol, SecurityServiceBase


class EncryptionConfig(BaseModel):
    """Configuration for encryption service."""

    master_key: SecretStr
    key_rotation_days: int = DEFAULT_KEY_EXPIRY_DAYS
    pbkdf2_iterations: int = 100000


class EncryptionService(SecurityServiceBase, EncryptionProtocol):
    """Implementation of the encryption service."""

    def __init__(self, config: EncryptionConfig, key_storage: KeyStorageProtocol):
        """Initialize the encryption service."""
        super().__init__(key_storage)
        self.config = config
        self._master_key = self._derive_key(
            config.master_key.get_secret_value().encode(), os.urandom(16)
        )

    def _derive_key(self, master_key: bytes, salt: bytes) -> bytes:
        """Derive an encryption key from the master key."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.config.pbkdf2_iterations,
        )
        return kdf.derive(master_key)

    async def encrypt(self, data: bytes, key_id: Optional[str] = None) -> tuple[bytes, str]:
        """Encrypt data using the specified or a new key."""
        try:
            if key_id is None:
                key_data = os.urandom(MINIMUM_KEY_LENGTH)
                key_id = str(uuid4())
                await self.key_storage.store_key(key_id, key_data)
            else:
                key_data = await self.key_storage.retrieve_key(key_id)

            cipher = aead.AESGCM(key_data)
            nonce = os.urandom(12)
            encrypted = cipher.encrypt(nonce, data, None)
            return encrypted, key_id
        except Exception as e:
            raise EncryptionError(
                message=f"Encryption failed: {str(e)}",
                operation="encrypt",
                reason=str(e),
            ) from e

    async def decrypt(self, encrypted_data: bytes, key_id: str) -> bytes:
        """Decrypt data using the specified key."""
        try:
            key_data = await self.key_storage.retrieve_key(key_id)
            cipher = aead.AESGCM(key_data)
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]
            return cipher.decrypt(nonce, ciphertext, None)
        except KeyNotFoundError:
            raise KeyNotFoundError(key_id=key_id)
        except Exception as e:
            raise EncryptionError(
                message=f"Decryption failed: {str(e)}",
                operation="decrypt",
                reason=str(e),
            ) from e

    async def rotate_encryption(
        self, data: bytes, old_key_id: str, new_key_id: str
    ) -> tuple[bytes, str]:
        """Re-encrypt data using a new key."""
        try:
            decrypted = await self.decrypt(data, old_key_id)
            return await self.encrypt(decrypted, new_key_id)
        except Exception as e:
            raise KeyRotationError(
                message=f"Key rotation failed: {str(e)}",
                key_id=old_key_id,
                reason=str(e),
            ) from e
