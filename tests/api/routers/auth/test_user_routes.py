"""Tests for user-related authentication routes."""

from unittest.mock import patch

import pytest
from fastapi import status

from src.api.middleware.csrf import generate_csrf_token


@pytest.mark.asyncio
async def test_signup_success(client):
    """Test successful user signup."""
    # Arrange
    signup_data = {
        "email": "test@example.com",
        "password": "Test123!@#",
        "name": "Test User",
    }

    with patch("src.api.middleware.csrf.generate_csrf_token", return_value="new_csrf_token"):
        # Act
        response = await client.post("/auth/signup", json=signup_data)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["access_token"] == "test_access_token"
    assert response.json()["token_type"] == "bearer"
    assert response.json()["user"]["id"] == "test_user_id"

    # Check cookies
    cookies = response.cookies
    assert "csrf_token" in cookies
    assert cookies["csrf_token"].value == "new_csrf_token"


@pytest.mark.asyncio
async def test_signup_with_csrf(client, mock_csrf_token):
    """Test signup with existing CSRF token."""
    # Arrange
    signup_data = {
        "email": "test@example.com",
        "password": "Test123!@#",
        "name": "Test User",
    }

    # Act
    response = await client.post(
        "/auth/signup",
        json=signup_data,
        cookies={"csrf_token": mock_csrf_token},
        headers={"X-CSRF-Token": mock_csrf_token},
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_signin_success(client):
    """Test successful user signin."""
    # Arrange
    signin_data = {
        "email": "test@example.com",
        "password": "Test123!@#",
    }

    with patch("src.api.middleware.csrf.generate_csrf_token", return_value="new_csrf_token"):
        # Act
        response = await client.post("/auth/signin", json=signin_data)

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
async def test_signin_invalid_credentials(client, mock_supabase_client):
    """Test signin with invalid credentials."""
    # Arrange
    signin_data = {
        "email": "test@example.com",
        "password": "wrong_password",
    }
    mock_supabase_client.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")

    # Act
    response = await client.post("/auth/signin", json=signin_data)

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_signout_success(client):
    """Test successful user signout."""
    # Act
    response = await client.post("/auth/signout")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Successfully signed out"

    # Check cookies are cleared
    cookies = response.cookies
    assert "access_token" not in cookies
    assert "refresh_token" not in cookies
    assert "csrf_token" not in cookies


@pytest.mark.asyncio
async def test_reset_password_success(client):
    """Test successful password reset request."""
    # Arrange
    reset_data = {"email": "test@example.com"}

    # Act
    response = await client.post("/auth/reset-password", json=reset_data)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Password reset email sent"


@pytest.mark.asyncio
async def test_get_current_user_success(client):
    """Test getting current user profile."""
    # Act
    response = await client.get("/auth/me")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == "test_user_id"
    assert response.json()["email"] == "test@example.com"
    assert response.json()["name"] == "Test User"


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client, mock_supabase_client):
    """Test getting current user when unauthorized."""
    # Arrange
    mock_supabase_client.auth.get_user.side_effect = Exception("Not authenticated")

    # Act
    response = await client.get("/auth/me")

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"
