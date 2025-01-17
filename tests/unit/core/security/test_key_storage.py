"""Unit tests for key storage functionality."""

import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import SecretStr

from src.core.security.encryption import EncryptionKey, KeyStatus
from src.core.security.key_storage import FileKeyStorage, KeyStorageConfig, KeyStorageError


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
def key_storage(storage_config):
    """Create test key storage."""
    return FileKeyStorage(storage_config)


@pytest.fixture
def test_key():
    """Create test encryption key."""
    return EncryptionKey(
        id=uuid4(),
        key_data=SecretStr("test-key-data"),
        created_at=datetime.utcnow(),
        expires_at=None,
        status=KeyStatus.ACTIVE,
        version=1,
    )


@pytest.mark.asyncio
async def test_directory_creation(storage_config, temp_dir):
    """Test storage directory creation."""
    storage = FileKeyStorage(storage_config)

    # Check directories were created with storage instance
    assert storage.config.storage_dir.exists()
    assert storage.config.backup_dir.exists()

    # Check directory permissions
    assert storage.config.storage_dir.stat().st_mode & 0o777 == 0o700
    assert storage.config.backup_dir.stat().st_mode & 0o777 == 0o700


@pytest.mark.asyncio
async def test_key_storage_and_retrieval(key_storage, test_key):
    """Test storing and retrieving keys."""
    # Store key
    await key_storage.store_key(test_key)

    # Load keys
    keys = await key_storage.load_keys()
    assert test_key.id in keys

    loaded_key = keys[test_key.id]
    assert loaded_key.id == test_key.id
    assert loaded_key.key_data == test_key.key_data
    assert loaded_key.status == test_key.status
    assert loaded_key.version == test_key.version


@pytest.mark.asyncio
async def test_key_backup(key_storage, test_key):
    """Test key backup functionality."""
    # Store key multiple times
    await key_storage.store_key(test_key)
    test_key.version = 2
    await key_storage.store_key(test_key)
    test_key.version = 3
    await key_storage.store_key(test_key)

    # Check backup files
    backup_files = list(key_storage.config.backup_dir.glob(f"{test_key.id}_*.key"))
    assert len(backup_files) == key_storage.config.max_backup_count

    # Verify oldest backup was removed (max_backup_count = 2)
    backup_timestamps = [
        datetime.fromisoformat(f.name.split("_")[1].replace(".key", "")) for f in backup_files
    ]
    assert len(backup_timestamps) == 2
    assert backup_timestamps[1] > backup_timestamps[0]


@pytest.mark.asyncio
async def test_key_status_update(key_storage, test_key):
    """Test updating key status."""
    # Store key
    await key_storage.store_key(test_key)

    # Update status
    new_status = KeyStatus.DISABLED
    await key_storage.update_key_status(test_key.id, new_status)

    # Verify status was updated
    keys = await key_storage.load_keys()
    assert keys[test_key.id].status == new_status


@pytest.mark.asyncio
async def test_key_deletion(key_storage, test_key):
    """Test secure key deletion."""
    # Store key
    await key_storage.store_key(test_key)

    # Create backup
    test_key.version = 2
    await key_storage.store_key(test_key)

    # Delete key
    await key_storage.delete_key(test_key.id)

    # Verify key file is deleted
    key_path = key_storage._get_key_path(test_key.id)
    assert not key_path.exists()

    # Verify backup files are deleted
    backup_files = list(key_storage.config.backup_dir.glob(f"{test_key.id}_*.key"))
    assert len(backup_files) == 0


@pytest.mark.asyncio
async def test_atomic_writes(storage_config, test_key):
    """Test atomic write functionality."""
    # Enable atomic writes
    storage_config.enable_atomic_writes = True
    storage = FileKeyStorage(storage_config)

    # Store key
    await storage.store_key(test_key)

    # Verify no temporary files remain
    temp_files = list(storage_config.storage_dir.glob("*.tmp"))
    assert len(temp_files) == 0


@pytest.mark.asyncio
async def test_error_handling(key_storage):
    """Test error handling."""
    # Test updating non-existent key
    with pytest.raises(KeyStorageError, match="Key .* not found"):
        await key_storage.update_key_status(uuid4(), KeyStatus.DISABLED)

    # Test deleting non-existent key
    with pytest.raises(KeyStorageError, match="Key .* not found"):
        await key_storage.delete_key(uuid4())


@pytest.mark.asyncio
async def test_key_loading_with_invalid_files(key_storage, test_key):
    """Test loading keys with invalid files present."""
    # Store valid key
    await key_storage.store_key(test_key)

    # Create invalid key file
    invalid_path = key_storage.config.storage_dir / "invalid.key"
    invalid_path.write_bytes(b"invalid data")

    # Should load valid key and skip invalid
    keys = await key_storage.load_keys()
    assert len(keys) == 1
    assert test_key.id in keys
