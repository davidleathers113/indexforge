"""Tests for authentication helper utilities."""

import secrets
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
import pytest

from src.api.config import Settings
from src.api.utils.auth_helpers import get_oauth_settings, refresh_auth_tokens, validate_csrf


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    mock = AsyncMock()
    mock.auth = AsyncMock()
    return mock


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    return Settings(
        google_client_id="test_google_id",
        google_client_secret="test_google_secret",
        github_client_id="test_github_id",
        github_client_secret="test_github_secret",
        oauth_redirect_url="http://localhost:8000/auth/callback",
        supabase_url="http://localhost:54321",
        supabase_key="test_key",
        supabase_jwt_secret="test_secret",
    )


@pytest.mark.asyncio
async def test_validate_csrf_with_valid_tokens():
    """Test CSRF validation with valid tokens."""
    # Arrange
    csrf_token = "test_token"
    x_csrf_token = "test_token"

    # Act & Assert
    with patch("src.api.middleware.csrf.validate_csrf_token") as mock_validate:
        await validate_csrf(csrf_token, x_csrf_token)
        mock_validate.assert_called_once_with(csrf_token, x_csrf_token)


@pytest.mark.asyncio
async def test_validate_csrf_with_missing_tokens():
    """Test CSRF validation with missing tokens."""
    # Act & Assert
    with patch("src.api.middleware.csrf.validate_csrf_token") as mock_validate:
        await validate_csrf(None, None)
        mock_validate.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_auth_tokens_success(mock_supabase):
    """Test successful token refresh."""
    # Arrange
    mock_supabase.auth.refresh_session.return_value = MagicMock(
        session=MagicMock(access_token="new_token")
    )

    # Act
    with patch("src.api.middleware.csrf.generate_csrf_token", return_value="new_csrf"):
        access_token, csrf_token = await refresh_auth_tokens(mock_supabase)

    # Assert
    assert access_token == "new_token"
    assert csrf_token == "new_csrf"
    mock_supabase.auth.refresh_session.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_auth_tokens_failure(mock_supabase):
    """Test token refresh failure."""
    # Arrange
    mock_supabase.auth.refresh_session.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await refresh_auth_tokens(mock_supabase)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not refresh token"


@pytest.mark.asyncio
async def test_refresh_auth_tokens_error(mock_supabase):
    """Test token refresh error handling."""
    # Arrange
    mock_supabase.auth.refresh_session.side_effect = Exception("Test error")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await refresh_auth_tokens(mock_supabase)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token refresh failed"


def test_get_oauth_settings(mock_settings):
    """Test getting OAuth settings."""
    # Arrange
    test_state = "test_state"
    with patch("secrets.token_urlsafe", return_value=test_state):
        with patch("src.api.config.get_settings", return_value=mock_settings):
            # Act
            settings, state = get_oauth_settings()

            # Assert
            assert settings == mock_settings
            assert state == test_state
            secrets.token_urlsafe.assert_called_once_with(32)
