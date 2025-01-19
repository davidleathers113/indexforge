"""Unit tests for authentication functionality."""

import time
from unittest.mock import patch
from uuid import UUID

import jwt
from pydantic import SecretStr
import pytest

from src.core.security.auth import (
    AuthConfig,
    AuthenticationError,
    AuthenticationManager,
    InvalidCredentialsError,
    RateLimitExceededError,
    TokenExpiredError,
    User,
)


@pytest.fixture
def config():
    """Create test authentication configuration."""
    return AuthConfig(
        secret_key=SecretStr("test-secret-key"),
        token_expiry=60,
        max_failed_attempts=3,
        lockout_duration=30,
        rate_limit_window=5,
        rate_limit_max_requests=3,
    )


@pytest.fixture
def auth_manager(config):
    """Create test authentication manager."""
    return AuthenticationManager(config)


@pytest.fixture
async def test_user(auth_manager):
    """Create test user."""
    return await auth_manager.create_user(
        email="test@example.com",
        password="Test1234!@#$",
    )


def test_user_model_validation():
    """Test user model validation."""
    # Valid user
    user = User(
        id=UUID("00000000-0000-0000-0000-000000000000"),
        email="test@example.com",
        password_hash="0" * 128,
        salt="test-salt",
    )
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.failed_attempts == 0
    assert user.lockout_until is None

    # Invalid password hash
    with pytest.raises(ValueError, match="Invalid password hash format"):
        User(
            id=UUID("00000000-0000-0000-0000-000000000000"),
            email="test@example.com",
            password_hash="invalid",
            salt="test-salt",
        )

    # Invalid email
    with pytest.raises(ValueError, match="value is not a valid email address"):
        User(
            id=UUID("00000000-0000-0000-0000-000000000000"),
            email="invalid-email",
            password_hash="0" * 128,
            salt="test-salt",
        )


def test_password_validation(auth_manager):
    """Test password validation rules."""
    # Too short
    with pytest.raises(ValueError, match="must be at least 12 characters"):
        auth_manager.validate_password_strength("short")

    # Missing special character
    with pytest.raises(ValueError, match="must contain at least one special character"):
        auth_manager.validate_password_strength("TestPassword123")

    # Missing number
    with pytest.raises(ValueError, match="must contain at least one number"):
        auth_manager.validate_password_strength("TestPassword!@#")

    # Missing uppercase
    with pytest.raises(ValueError, match="must contain at least one uppercase letter"):
        auth_manager.validate_password_strength("testpassword123!@#")

    # Missing lowercase
    with pytest.raises(ValueError, match="must contain at least one lowercase letter"):
        auth_manager.validate_password_strength("TESTPASSWORD123!@#")

    # Valid password
    auth_manager.validate_password_strength("TestPassword123!@#")


@pytest.mark.asyncio
async def test_user_creation(auth_manager):
    """Test user creation."""
    user = await auth_manager.create_user(
        email="test@example.com",
        password="TestPassword123!@#",
    )
    assert isinstance(user.id, UUID)
    assert user.email == "test@example.com"
    assert len(user.password_hash) == 128
    assert user.salt
    assert user.is_active is True
    assert user.failed_attempts == 0
    assert user.lockout_until is None


@pytest.mark.asyncio
async def test_authentication(auth_manager, test_user):
    """Test user authentication."""
    # Successful authentication
    token = await auth_manager.authenticate(
        test_user,
        "Test1234!@#$",
        "test-ip",
    )
    assert isinstance(token, str)

    # Failed authentication
    with pytest.raises(InvalidCredentialsError):
        await auth_manager.authenticate(
            test_user,
            "wrong-password",
            "test-ip",
        )

    # Check failed attempts increment
    assert test_user.failed_attempts == 1

    # Test account lockout
    for _ in range(auth_manager.config.max_failed_attempts - 1):
        with pytest.raises(InvalidCredentialsError):
            await auth_manager.authenticate(
                test_user,
                "wrong-password",
                "test-ip",
            )

    assert test_user.lockout_until is not None
    assert test_user.failed_attempts == auth_manager.config.max_failed_attempts

    # Test authentication during lockout
    with pytest.raises(InvalidCredentialsError, match="Account is locked until"):
        await auth_manager.authenticate(
            test_user,
            "Test1234!@#$",
            "test-ip",
        )

    # Test successful authentication resets failed attempts
    test_user.lockout_until = None
    token = await auth_manager.authenticate(
        test_user,
        "Test1234!@#$",
        "test-ip",
    )
    assert isinstance(token, str)
    assert test_user.failed_attempts == 0
    assert test_user.last_login is not None


@pytest.mark.asyncio
async def test_rate_limiting(auth_manager, test_user):
    """Test authentication rate limiting."""
    # Make requests up to limit
    for _ in range(auth_manager.config.rate_limit_max_requests):
        with pytest.raises(InvalidCredentialsError):
            await auth_manager.authenticate(
                test_user,
                "wrong-password",
                "test-ip",
            )

    # Next request should be rate limited
    with pytest.raises(RateLimitExceededError):
        await auth_manager.authenticate(
            test_user,
            "Test1234!@#$",
            "test-ip",
        )

    # Wait for rate limit window to expire
    time.sleep(auth_manager.config.rate_limit_window + 1)

    # Should be able to authenticate again
    token = await auth_manager.authenticate(
        test_user,
        "Test1234!@#$",
        "test-ip",
    )
    assert isinstance(token, str)


@pytest.mark.asyncio
async def test_token_validation(auth_manager, test_user):
    """Test authentication token validation."""
    # Generate token
    token = await auth_manager.authenticate(
        test_user,
        "Test1234!@#$",
        "test-ip",
    )

    # Valid token
    user_id = await auth_manager.validate_authentication(token)
    assert user_id == test_user.id

    # Expired token
    with patch("jwt.decode") as mock_decode:
        mock_decode.side_effect = jwt.ExpiredSignatureError()
        with pytest.raises(TokenExpiredError):
            await auth_manager.validate_authentication(token)

    # Invalid token
    with pytest.raises(AuthenticationError):
        await auth_manager.validate_authentication("invalid-token")


@pytest.mark.asyncio
async def test_concurrent_authentication(auth_manager, test_user):
    """Test concurrent authentication requests."""
    import asyncio

    # Create multiple authentication requests
    async def auth_request():
        return await auth_manager.authenticate(
            test_user,
            "Test1234!@#$",
            "test-ip",
        )

    # Should handle concurrent requests without race conditions
    results = await asyncio.gather(
        *[auth_request() for _ in range(5)],
        return_exceptions=True,
    )

    # First request should succeed, others should be rate limited
    assert any(isinstance(r, str) for r in results)  # At least one token
    assert any(isinstance(r, RateLimitExceededError) for r in results)  # Some rate limited
