"""Unit tests for key storage functionality."""

import os
import uuid
from datetime import datetime

import pytest
from pydantic import SecretStr

from src.core.security.common import MINIMUM_KEY_LENGTH
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
def test_key_data():
    """Create test key data."""
    return os.urandom(MINIMUM_KEY_LENGTH)


@pytest.fixture
def test_key_id():
    """Create test key ID."""
    return str(uuid.uuid4())


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
async def test_key_storage_and_retrieval(key_storage, test_key_data, test_key_id):
    """Test storing and retrieving keys."""
    # Store key
    await key_storage.store_key(test_key_id, test_key_data)

    # Retrieve key
    retrieved_key_data = await key_storage.retrieve_key(test_key_id)
    assert retrieved_key_data == test_key_data


@pytest.mark.asyncio
async def test_key_backup(key_storage, test_key_id):
    """Test key backup functionality."""
    # Store key multiple times with different data
    key_data_1 = os.urandom(MINIMUM_KEY_LENGTH)
    key_data_2 = os.urandom(MINIMUM_KEY_LENGTH)
    key_data_3 = os.urandom(MINIMUM_KEY_LENGTH)

    await key_storage.store_key(test_key_id, key_data_1)
    await key_storage.store_key(test_key_id, key_data_2)
    await key_storage.store_key(test_key_id, key_data_3)

    # Check backup files
    backup_files = list(key_storage.config.backup_dir.glob(f"{test_key_id}_*.key"))
    assert len(backup_files) == key_storage.config.max_backup_count

    # Verify oldest backup was removed (max_backup_count = 2)
    backup_timestamps = [
        datetime.fromisoformat(f.name.split("_")[1].replace(".key", "")) for f in backup_files
    ]
    assert len(backup_timestamps) == 2
    assert backup_timestamps[1] > backup_timestamps[0]


@pytest.mark.asyncio
async def test_key_rotation(key_storage, test_key_id, test_key_data):
    """Test key rotation functionality."""
    # Store initial key
    await key_storage.store_key(test_key_id, test_key_data)

    # Rotate key
    new_key_data = await key_storage.rotate_key(test_key_id)

    # Verify new key is different
    assert new_key_data != test_key_data
    assert len(new_key_data) >= MINIMUM_KEY_LENGTH

    # Verify retrieved key matches new key
    retrieved_key_data = await key_storage.retrieve_key(test_key_id)
    assert retrieved_key_data == new_key_data

    # Verify backup was created
    backup_files = list(key_storage.config.backup_dir.glob(f"{test_key_id}_*.key"))
    assert len(backup_files) == 1


@pytest.mark.asyncio
async def test_key_deletion(key_storage, test_key_id, test_key_data):
    """Test secure key deletion."""
    # Store key
    await key_storage.store_key(test_key_id, test_key_data)

    # Create backup by storing again
    await key_storage.store_key(test_key_id, os.urandom(MINIMUM_KEY_LENGTH))

    # Delete key
    await key_storage.delete_key(test_key_id)

    # Verify key file is deleted
    key_path = key_storage._get_key_path(test_key_id)
    assert not key_path.exists()

    # Verify backup files are deleted
    backup_files = list(key_storage.config.backup_dir.glob(f"{test_key_id}_*.key"))
    assert len(backup_files) == 0


@pytest.mark.asyncio
async def test_atomic_writes(storage_config, test_key_id, test_key_data):
    """Test atomic write functionality."""
    # Enable atomic writes
    storage_config.enable_atomic_writes = True
    storage = FileKeyStorage(storage_config)

    # Store key
    await storage.store_key(test_key_id, test_key_data)

    # Verify no temporary files remain
    temp_files = list(storage_config.storage_dir.glob("*.tmp"))
    assert len(temp_files) == 0


@pytest.mark.asyncio
async def test_error_handling(key_storage, test_key_id):
    """Test error handling."""
    # Test retrieving non-existent key
    with pytest.raises(KeyStorageError, match="Key .* not found"):
        await key_storage.retrieve_key(test_key_id)

    # Test deleting non-existent key
    with pytest.raises(KeyStorageError, match="Key .* not found"):
        await key_storage.delete_key(test_key_id)

    # Test storing invalid key data
    with pytest.raises(
        KeyStorageError, match=f"Key data must be at least {MINIMUM_KEY_LENGTH} bytes"
    ):
        await key_storage.store_key(test_key_id, b"too short")


@pytest.mark.asyncio
async def test_key_storage_encryption(key_storage, test_key_id, test_key_data):
    """Test that stored keys are properly encrypted."""
    # Store key
    await key_storage.store_key(test_key_id, test_key_data)

    # Read raw file contents
    key_path = key_storage._get_key_path(test_key_id)
    encrypted_data = key_path.read_bytes()

    # Verify data is encrypted (not matching original)
    assert encrypted_data != test_key_data
    assert len(encrypted_data) > len(test_key_data)  # Encrypted data should be longer due to IV/tag

    # Verify we can still retrieve and decrypt
    retrieved_data = await key_storage.retrieve_key(test_key_id)
    assert retrieved_data == test_key_data
