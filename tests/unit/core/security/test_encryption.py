"""Unit tests for encryption functionality."""

from datetime import datetime
import time
from uuid import UUID

from pydantic import SecretStr
import pytest

from src.core.security.encryption import (
    DecryptionError,
    EncryptedData,
    EncryptionConfig,
    EncryptionKeyNotFoundError,
    EncryptionManager,
    KeyGenerationError,
    KeyStatus,
)


@pytest.fixture
def config():
    """Create test encryption configuration."""
    return EncryptionConfig(
        master_key=SecretStr("test-master-key-that-is-sufficiently-long"),
        key_rotation_days=1,
        min_key_retention_days=2,
        pbkdf2_iterations=1000,  # Lower for tests
    )


@pytest.fixture
def encryption_manager(config):
    """Create test encryption manager."""
    return EncryptionManager(config)


@pytest.mark.asyncio
async def test_key_creation(encryption_manager):
    """Test encryption key creation."""
    key = await encryption_manager.create_key()
    assert isinstance(key.id, UUID)
    assert isinstance(key.key_data, SecretStr)
    assert isinstance(key.created_at, datetime)
    assert isinstance(key.expires_at, datetime)
    assert key.status == KeyStatus.ACTIVE
    assert key.version == 1
    assert key.key_type == "AES256-GCM"

    # Key should be stored and set as active
    assert key.id in encryption_manager._keys
    assert encryption_manager._active_key == key.id


@pytest.mark.asyncio
async def test_key_rotation(encryption_manager):
    """Test encryption key rotation."""
    # Create initial key
    key1 = await encryption_manager.create_key()
    assert key1.status == KeyStatus.ACTIVE

    # Wait to ensure different timestamps
    time.sleep(0.1)

    # Rotate keys
    await encryption_manager.rotate_keys()
    key2 = encryption_manager._keys[encryption_manager._active_key]

    # Check key states
    assert key1.status == KeyStatus.ENABLED
    assert key2.status == KeyStatus.ACTIVE
    assert key1.id != key2.id
    assert key2.version > key1.version

    # Wait for retention period
    time.sleep(2.1)  # Just over retention period

    # Rotate again
    await encryption_manager.rotate_keys()
    key3 = encryption_manager._keys[encryption_manager._active_key]

    # Check key states
    assert key1.status == KeyStatus.DISABLED
    assert key2.status == KeyStatus.ENABLED
    assert key3.status == KeyStatus.ACTIVE


@pytest.mark.asyncio
async def test_key_retrieval(encryption_manager):
    """Test encryption key retrieval."""
    key = await encryption_manager.create_key()

    # Get existing key
    retrieved_key = await encryption_manager.get_key(key.id)
    assert retrieved_key.id == key.id
    assert retrieved_key.key_data == key.key_data

    # Get non-existent key
    import uuid

    with pytest.raises(EncryptionKeyNotFoundError):
        await encryption_manager.get_key(uuid.uuid4())

    # Get deleted key
    key.status = KeyStatus.DELETED
    with pytest.raises(EncryptionKeyNotFoundError):
        await encryption_manager.get_key(key.id)


@pytest.mark.asyncio
async def test_encryption_decryption(encryption_manager):
    """Test data encryption and decryption."""
    data = b"test data to encrypt"

    # Encrypt data
    encrypted = await encryption_manager.encrypt(data)
    assert isinstance(encrypted, EncryptedData)
    assert isinstance(encrypted.key_id, UUID)
    assert isinstance(encrypted.nonce, bytes)
    assert isinstance(encrypted.ciphertext, bytes)
    assert isinstance(encrypted.tag, bytes)
    assert isinstance(encrypted.version, int)
    assert isinstance(encrypted.created_at, datetime)

    # Decrypt data
    decrypted = await encryption_manager.decrypt(encrypted)
    assert decrypted == data

    # Decrypt with wrong key ID
    import uuid

    bad_encrypted = EncryptedData(
        key_id=uuid.uuid4(),
        nonce=encrypted.nonce,
        ciphertext=encrypted.ciphertext,
        tag=encrypted.tag,
        version=encrypted.version,
        created_at=encrypted.created_at,
    )
    with pytest.raises(DecryptionError):
        await encryption_manager.decrypt(bad_encrypted)

    # Decrypt with disabled key
    key = encryption_manager._keys[encrypted.key_id]
    key.status = KeyStatus.DISABLED
    with pytest.raises(DecryptionError, match="Key is disabled"):
        await encryption_manager.decrypt(encrypted)


@pytest.mark.asyncio
async def test_key_derivation(encryption_manager):
    """Test key derivation."""
    # Test with valid master key
    salt = b"test-salt"
    key_bytes = encryption_manager._derive_key("test-key", salt)
    assert isinstance(key_bytes, bytes)
    assert len(key_bytes) == 32  # 256 bits

    # Test with empty master key
    with pytest.raises(KeyGenerationError):
        encryption_manager._derive_key("", salt)


@pytest.mark.asyncio
async def test_encryption_without_active_key(encryption_manager):
    """Test encryption when no active key exists."""
    data = b"test data"

    # Encrypt without existing key
    assert encryption_manager._active_key is None
    encrypted = await encryption_manager.encrypt(data)

    # Should create key and encrypt successfully
    assert encryption_manager._active_key is not None
    decrypted = await encryption_manager.decrypt(encrypted)
    assert decrypted == data


@pytest.mark.asyncio
async def test_multiple_key_rotations(encryption_manager):
    """Test multiple key rotations and encryption/decryption."""
    data = b"test data"

    # Create multiple generations of keys
    encrypted_data = []
    for _ in range(3):
        encrypted = await encryption_manager.encrypt(data)
        encrypted_data.append(encrypted)
        await encryption_manager.rotate_keys()

    # Should be able to decrypt with all keys
    for encrypted in encrypted_data:
        decrypted = await encryption_manager.decrypt(encrypted)
        assert decrypted == data


@pytest.mark.asyncio
async def test_concurrent_encryption(encryption_manager):
    """Test concurrent encryption operations."""
    import asyncio

    # Create multiple encryption tasks
    data = b"test data"
    tasks = [encryption_manager.encrypt(data) for _ in range(5)]

    # Run concurrently
    results = await asyncio.gather(*tasks)

    # All should encrypt successfully
    for encrypted in results:
        assert isinstance(encrypted, EncryptedData)
        decrypted = await encryption_manager.decrypt(encrypted)
        assert decrypted == data
