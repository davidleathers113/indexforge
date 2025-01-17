"""Unit tests for encryption manager with key storage integration."""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import SecretStr

from src.core.security.encryption import (
    EncryptionConfig,
    EncryptionKey,
    EncryptionKeyNotFoundError,
    EncryptionManager,
    KeyStatus,
)
from src.core.security.key_storage import KeyStorageConfig


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
def encryption_config(storage_config):
    """Create test encryption configuration."""
    return EncryptionConfig(
        master_key=SecretStr("test-master-key-that-is-sufficiently-long"),
        key_rotation_days=1,
        min_key_retention_days=2,
        pbkdf2_iterations=1000,  # Lower for tests
        storage=storage_config,
    )


@pytest.fixture
async def encryption_manager(encryption_config):
    """Create test encryption manager."""
    manager = EncryptionManager(encryption_config)
    await manager._init_storage()
    return manager


@pytest.mark.asyncio
async def test_key_persistence(encryption_manager, temp_dir):
    """Test key persistence across manager instances."""
    # Create key with first manager
    key1 = await encryption_manager.create_key()
    assert key1.status == KeyStatus.ACTIVE

    # Create new manager instance
    new_manager = EncryptionManager(encryption_manager.config)
    await new_manager._init_storage()

    # Verify key is loaded
    loaded_key = await new_manager.get_key(key1.id)
    assert loaded_key.id == key1.id
    assert loaded_key.key_data == key1.key_data
    assert loaded_key.status == key1.status
    assert loaded_key.version == key1.version
    assert new_manager._active_key == key1.id


@pytest.mark.asyncio
async def test_key_rotation_persistence(encryption_manager):
    """Test key rotation with persistent storage."""
    # Create initial key
    key1 = await encryption_manager.create_key()
    assert key1.status == KeyStatus.ACTIVE

    # Wait to ensure different timestamps
    await asyncio.sleep(0.1)

    # Rotate keys
    await encryption_manager.rotate_keys()
    key2 = encryption_manager._keys[encryption_manager._active_key]

    # Create new manager instance
    new_manager = EncryptionManager(encryption_manager.config)
    await new_manager._init_storage()

    # Verify key states are preserved
    loaded_key1 = await new_manager.get_key(key1.id)
    loaded_key2 = await new_manager.get_key(key2.id)

    assert loaded_key1.status == KeyStatus.ENABLED
    assert loaded_key2.status == KeyStatus.ACTIVE
    assert new_manager._active_key == key2.id


@pytest.mark.asyncio
async def test_key_deletion_persistence(encryption_manager):
    """Test key deletion with persistent storage."""
    # Create and rotate keys multiple times
    key1 = await encryption_manager.create_key()
    await asyncio.sleep(0.1)
    await encryption_manager.rotate_keys()
    key2 = encryption_manager._keys[encryption_manager._active_key]

    # Wait for retention period
    await asyncio.sleep(2.1)  # Just over retention period

    # Rotate again to trigger deletion
    await encryption_manager.rotate_keys()

    # Create new manager instance
    new_manager = EncryptionManager(encryption_manager.config)
    await new_manager._init_storage()

    # Verify key1 is deleted and key2 is disabled
    with pytest.raises(EncryptionKeyNotFoundError):
        await new_manager.get_key(key1.id)

    loaded_key2 = await new_manager.get_key(key2.id)
    assert loaded_key2.status == KeyStatus.DISABLED


@pytest.mark.asyncio
async def test_encryption_with_persistent_keys(encryption_manager):
    """Test encryption/decryption with persistent keys."""
    # Create key and encrypt data
    data = b"test data to encrypt"
    encrypted = await encryption_manager.encrypt(data)

    # Create new manager instance
    new_manager = EncryptionManager(encryption_manager.config)
    await new_manager._init_storage()

    # Decrypt with new manager
    decrypted = await new_manager.decrypt(encrypted)
    assert decrypted == data


@pytest.mark.asyncio
async def test_version_tracking(encryption_manager):
    """Test version tracking across manager instances."""
    # Create multiple keys
    key1 = await encryption_manager.create_key()
    await encryption_manager.rotate_keys()
    key2 = encryption_manager._keys[encryption_manager._active_key]

    # Create new manager instance
    new_manager = EncryptionManager(encryption_manager.config)
    await new_manager._init_storage()

    # Create another key
    key3 = await new_manager.create_key()

    # Verify version progression
    assert key1.version < key2.version < key3.version


@pytest.mark.asyncio
async def test_storage_initialization_error_handling(encryption_config, temp_dir):
    """Test handling of storage initialization errors."""
    # Create invalid storage path
    encryption_config.storage.storage_dir = Path("/nonexistent/path")

    # Should handle initialization error gracefully
    manager = EncryptionManager(encryption_config)
    with pytest.raises(Exception):
        await manager._init_storage()

    # Should still be able to create and use keys in memory
    key = await manager.create_key()
    assert key.status == KeyStatus.ACTIVE
