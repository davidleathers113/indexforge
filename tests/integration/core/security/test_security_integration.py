"""Integration tests for security services.

This module tests the interaction between encryption and key storage services,
verifying proper integration and end-to-end functionality.
"""

import asyncio
import os
from typing import AsyncGenerator

import pytest
from pydantic import SecretStr

from src.core.security.common import (
    MINIMUM_KEY_LENGTH,
    EncryptionError,
    KeyNotFoundError,
    KeyRotationError,
)
from src.core.security.encryption import EncryptionConfig, EncryptionService
from src.core.security.key_storage import FileKeyStorage, KeyStorageConfig


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for testing."""
    return tmp_path


@pytest.fixture
def storage_config(temp_dir):
    """Create test storage configuration."""
    return KeyStorageConfig(
        storage_dir=temp_dir / "keys",
        backup_dir=temp_dir / "backups",
        storage_key=SecretStr("test-storage-key-that-is-sufficiently-long"),
        max_backup_count=2,
        enable_atomic_writes=True,
    )


@pytest.fixture
def encryption_config():
    """Create test encryption configuration."""
    return EncryptionConfig(
        master_key=SecretStr("test-master-key-that-is-sufficiently-long"),
        key_rotation_days=90,
        pbkdf2_iterations=1000,  # Reduced for testing
    )


@pytest.fixture
async def key_storage(storage_config) -> AsyncGenerator[FileKeyStorage, None]:
    """Create and cleanup key storage."""
    storage = FileKeyStorage(storage_config)
    yield storage
    # Cleanup: securely delete all test keys
    for key_file in storage.config.storage_dir.glob("*.key"):
        with open(key_file, "wb") as f:
            f.write(os.urandom(1024))
            f.flush()
            os.fsync(f.fileno())
        key_file.unlink()
    for backup_file in storage.config.backup_dir.glob("*.key"):
        backup_file.unlink()


@pytest.fixture
def encryption_service(encryption_config, key_storage):
    """Create encryption service with key storage."""
    return EncryptionService(encryption_config, key_storage)


@pytest.fixture
def test_data():
    """Create test data for encryption."""
    return b"test data for encryption"


@pytest.mark.asyncio
async def test_end_to_end_encryption(encryption_service, test_data):
    """Test complete encryption flow from storage through encryption/decryption."""
    # Encrypt data (should create and store new key)
    encrypted_data, key_id = await encryption_service.encrypt(test_data)

    # Verify key was stored
    key_data = await encryption_service.key_storage.retrieve_key(key_id)
    assert len(key_data) >= MINIMUM_KEY_LENGTH

    # Decrypt data
    decrypted_data = await encryption_service.decrypt(encrypted_data, key_id)
    assert decrypted_data == test_data


@pytest.mark.asyncio
async def test_key_rotation_flow(encryption_service, test_data):
    """Test key rotation with data re-encryption."""
    # Initial encryption
    encrypted_data, old_key_id = await encryption_service.encrypt(test_data)

    # Generate new key through rotation
    new_key_data = await encryption_service.key_storage.rotate_key(old_key_id)
    assert len(new_key_data) >= MINIMUM_KEY_LENGTH

    # Re-encrypt data with rotated key
    new_encrypted_data, _ = await encryption_service.rotate_encryption(
        encrypted_data, old_key_id, old_key_id
    )

    # Verify decryption with rotated key
    decrypted_data = await encryption_service.decrypt(new_encrypted_data, old_key_id)
    assert decrypted_data == test_data


@pytest.mark.asyncio
async def test_key_deletion_flow(encryption_service, test_data):
    """Test proper handling of key deletion in encryption workflow."""
    # Encrypt data
    encrypted_data, key_id = await encryption_service.encrypt(test_data)

    # Delete key
    await encryption_service.key_storage.delete_key(key_id)

    # Verify decryption fails
    with pytest.raises(KeyNotFoundError):
        await encryption_service.decrypt(encrypted_data, key_id)


@pytest.mark.asyncio
async def test_concurrent_operations(encryption_service):
    """Test concurrent encryption operations."""
    test_data_set = [os.urandom(100) for _ in range(10)]

    # Encrypt multiple pieces of data concurrently
    encryption_tasks = [encryption_service.encrypt(data) for data in test_data_set]
    results = await asyncio.gather(*encryption_tasks)

    # Verify all encryptions succeeded
    for (encrypted, key_id), original_data in zip(results, test_data_set):
        decrypted = await encryption_service.decrypt(encrypted, key_id)
        assert decrypted == original_data


@pytest.mark.asyncio
async def test_error_propagation(encryption_service, test_data):
    """Test error handling and propagation between services."""
    # Test with invalid key ID
    with pytest.raises(KeyNotFoundError):
        await encryption_service.decrypt(test_data, "nonexistent-key")

    # Test with invalid encrypted data
    encrypted_data, key_id = await encryption_service.encrypt(test_data)
    with pytest.raises(EncryptionError):
        await encryption_service.decrypt(b"invalid-data", key_id)

    # Test rotation with invalid keys
    with pytest.raises(KeyRotationError):
        await encryption_service.rotate_encryption(
            encrypted_data, "nonexistent-key", "new-nonexistent-key"
        )


@pytest.mark.asyncio
async def test_key_reuse(encryption_service, test_data):
    """Test using the same key for multiple operations."""
    # Initial encryption
    encrypted_data1, key_id = await encryption_service.encrypt(test_data)

    # Use same key for another encryption
    encrypted_data2, reused_key_id = await encryption_service.encrypt(b"different data", key_id)

    assert key_id == reused_key_id

    # Verify both decryptions work
    assert await encryption_service.decrypt(encrypted_data1, key_id) == test_data
    assert await encryption_service.decrypt(encrypted_data2, key_id) == b"different data"


@pytest.mark.asyncio
async def test_large_data_handling(encryption_service):
    """Test encryption/decryption of larger data blocks."""
    large_data = os.urandom(1024 * 1024)  # 1MB

    # Encrypt large data
    encrypted_data, key_id = await encryption_service.encrypt(large_data)

    # Verify decryption
    decrypted_data = await encryption_service.decrypt(encrypted_data, key_id)
    assert decrypted_data == large_data


@pytest.mark.asyncio
async def test_service_initialization(encryption_config, key_storage):
    """Test proper service initialization and configuration."""
    # Test with valid config
    service = EncryptionService(encryption_config, key_storage)
    assert service.key_storage is not None

    # Test with missing key storage
    with pytest.raises(ValueError):
        service = EncryptionService(encryption_config, None)
        _ = service.key_storage  # Should raise error

    # Test with invalid key storage
    with pytest.raises(TypeError):
        service = EncryptionService(encryption_config, object())  # type: ignore
