"""Tests for token-related authentication routes."""

from unittest.mock import patch

from fastapi import status
import pytest


@pytest.mark.asyncio
async def test_refresh_token_success(client, mock_csrf_token):
    """Test successful token refresh."""
    # Arrange
    with patch("src.api.middleware.csrf.generate_csrf_token", return_value="new_csrf_token"):
        # Act
        response = await client.post(
            "/auth/refresh",
            cookies={"csrf_token": mock_csrf_token},
            headers={"X-CSRF-Token": mock_csrf_token},
        )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["access_token"] == "test_access_token"
    assert response.json()["token_type"] == "bearer"
    assert response.json()["user"]["id"] == "test_user_id"

    # Check cookies
    cookies = response.cookies
    assert "csrf_token" in cookies
    assert cookies["csrf_token"].value == "new_csrf_token"


@pytest.mark.asyncio
async def test_refresh_token_missing_csrf(client):
    """Test token refresh with missing CSRF token."""
    # Act
    response = await client.post("/auth/refresh")

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_refresh_token_invalid_csrf(client, mock_csrf_token):
    """Test token refresh with invalid CSRF token."""
    # Act
    response = await client.post(
        "/auth/refresh",
        cookies={"csrf_token": mock_csrf_token},
        headers={"X-CSRF-Token": "invalid_token"},
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_refresh_token_refresh_failure(client, mock_csrf_token, mock_supabase_client):
    """Test token refresh when refresh fails."""
    # Arrange
    mock_supabase_client.auth.refresh_session.return_value = None

    # Act
    response = await client.post(
        "/auth/refresh",
        cookies={"csrf_token": mock_csrf_token},
        headers={"X-CSRF-Token": mock_csrf_token},
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Could not refresh token"


@pytest.mark.asyncio
async def test_refresh_token_error(client, mock_csrf_token, mock_supabase_client):
    """Test token refresh when an error occurs."""
    # Arrange
    mock_supabase_client.auth.refresh_session.side_effect = Exception("Test error")

    # Act
    response = await client.post(
        "/auth/refresh",
        cookies={"csrf_token": mock_csrf_token},
        headers={"X-CSRF-Token": mock_csrf_token},
    )

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Token refresh failed"
