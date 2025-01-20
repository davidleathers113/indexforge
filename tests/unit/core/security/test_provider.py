"""Unit tests for security service provider."""

import pytest
from pydantic import SecretStr

from src.core.security.encryption import EncryptionConfig
from src.core.security.key_storage import KeyStorageConfig
from src.core.security.provider import SecurityServiceError, SecurityServiceProvider
from src.core.types.service import ServiceError, ServiceState


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
def security_provider(encryption_config, storage_config):
    """Create security service provider."""
    return SecurityServiceProvider(encryption_config, storage_config)


@pytest.mark.asyncio
async def test_provider_initialization(security_provider):
    """Test provider initialization."""
    # Initial state
    assert security_provider.state == ServiceState.CREATED

    # Initialize services
    await security_provider.initialize()
    assert security_provider.state == ServiceState.RUNNING

    # Verify services are accessible
    assert security_provider.key_storage is not None
    assert security_provider.encryption is not None


@pytest.mark.asyncio
async def test_provider_cleanup(security_provider):
    """Test provider cleanup."""
    # Initialize first
    await security_provider.initialize()
    assert security_provider.state == ServiceState.RUNNING

    # Cleanup
    await security_provider.cleanup()
    assert security_provider.state == ServiceState.STOPPED

    # Verify services are cleaned up
    with pytest.raises(SecurityServiceError):
        _ = security_provider.key_storage
    with pytest.raises(SecurityServiceError):
        _ = security_provider.encryption


@pytest.mark.asyncio
async def test_provider_health_check(security_provider):
    """Test provider health check."""
    # Not initialized
    assert not await security_provider.health_check()

    # Initialize
    await security_provider.initialize()
    assert await security_provider.health_check()

    # After cleanup
    await security_provider.cleanup()
    assert not await security_provider.health_check()


@pytest.mark.asyncio
async def test_provider_error_handling(security_provider):
    """Test provider error handling."""
    # Try to access services before initialization
    with pytest.raises(SecurityServiceError):
        _ = security_provider.key_storage
    with pytest.raises(SecurityServiceError):
        _ = security_provider.encryption

    # Initialize with invalid config should fail
    bad_provider = SecurityServiceProvider(
        encryption_config=EncryptionConfig(
            master_key=SecretStr("too-short"),
            key_rotation_days=90,
            pbkdf2_iterations=1000,
        ),
        key_storage_config=storage_config,
    )
    with pytest.raises(SecurityServiceError):
        await bad_provider.initialize()
    assert bad_provider.state == ServiceState.ERROR


@pytest.mark.asyncio
async def test_provider_context_manager(encryption_config, storage_config):
    """Test provider as context manager."""
    async with SecurityServiceProvider(encryption_config, storage_config) as provider:
        assert provider.state == ServiceState.RUNNING
        assert await provider.health_check()
        assert provider.key_storage is not None
        assert provider.encryption is not None

    # After context exit
    assert provider.state == ServiceState.STOPPED
    with pytest.raises(SecurityServiceError):
        _ = provider.key_storage
