"""Tests for OAuth-related authentication routes."""

from unittest.mock import patch

from fastapi import status
import pytest


@pytest.mark.asyncio
async def test_oauth_signin_google_success(client):
    """Test successful OAuth sign-in initiation with Google."""
    # Arrange
    signin_data = {
        "provider": "google",
        "redirect_url": "http://localhost:3000/auth/callback",
    }

    # Act
    response = await client.post("/auth/oauth/signin", json=signin_data)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert "auth_url" in response.json()
    assert "google" in response.json()["auth_url"]
    assert "state" in response.json()


@pytest.mark.asyncio
async def test_oauth_signin_github_success(client):
    """Test successful OAuth sign-in initiation with GitHub."""
    # Arrange
    signin_data = {
        "provider": "github",
        "redirect_url": "http://localhost:3000/auth/callback",
    }

    # Act
    response = await client.post("/auth/oauth/signin", json=signin_data)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert "auth_url" in response.json()
    assert "github" in response.json()["auth_url"]
    assert "state" in response.json()


@pytest.mark.asyncio
async def test_oauth_signin_invalid_provider(client):
    """Test OAuth sign-in with invalid provider."""
    # Arrange
    signin_data = {
        "provider": "invalid",
        "redirect_url": "http://localhost:3000/auth/callback",
    }

    # Act
    response = await client.post("/auth/oauth/signin", json=signin_data)

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid OAuth provider"


@pytest.mark.asyncio
async def test_oauth_callback_google_success(client, mock_supabase_client):
    """Test successful OAuth callback from Google."""
    # Arrange
    state = "test_state"
    code = "test_auth_code"
    mock_supabase_client.auth.exchange_code_for_session.return_value = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "user": {
            "id": "test_user_id",
            "email": "test@example.com",
            "name": "Test User",
        },
    }

    with patch("src.api.middleware.csrf.generate_csrf_token", return_value="new_csrf_token"):
        # Act
        response = await client.get(f"/auth/oauth/callback/google?state={state}&code={code}")

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
async def test_oauth_callback_github_success(client, mock_supabase_client):
    """Test successful OAuth callback from GitHub."""
    # Arrange
    state = "test_state"
    code = "test_auth_code"
    mock_supabase_client.auth.exchange_code_for_session.return_value = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "user": {
            "id": "test_user_id",
            "email": "test@example.com",
            "name": "Test User",
        },
    }

    with patch("src.api.middleware.csrf.generate_csrf_token", return_value="new_csrf_token"):
        # Act
        response = await client.get(f"/auth/oauth/callback/github?state={state}&code={code}")

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
async def test_oauth_callback_invalid_state(client):
    """Test OAuth callback with invalid state parameter."""
    # Arrange
    state = "invalid_state"
    code = "test_auth_code"

    # Act
    response = await client.get(f"/auth/oauth/callback/google?state={state}&code={code}")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid state parameter"


@pytest.mark.asyncio
async def test_oauth_callback_missing_code(client):
    """Test OAuth callback with missing code parameter."""
    # Arrange
    state = "test_state"

    # Act
    response = await client.get(f"/auth/oauth/callback/google?state={state}")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Missing authorization code"


@pytest.mark.asyncio
async def test_oauth_callback_exchange_error(client, mock_supabase_client):
    """Test OAuth callback with token exchange error."""
    # Arrange
    state = "test_state"
    code = "test_auth_code"
    mock_supabase_client.auth.exchange_code_for_session.side_effect = Exception("Exchange failed")

    # Act
    response = await client.get(f"/auth/oauth/callback/google?state={state}&code={code}")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Failed to exchange authorization code for tokens"
