"""Test fixtures for authentication tests."""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.app import app


def pytest_configure(config):
    """Configure test environment."""
    # Clear any existing Supabase URLs from environment
    if "SUPABASE_URL" in os.environ:
        del os.environ["SUPABASE_URL"]

    # Set test environment
    os.environ.update(
        {
            "ENVIRONMENT": "test",
            # Supabase configuration - use local dev URLs
            "SUPABASE_URL": "http://localhost:54321",  # Supabase local dev API
            "SUPABASE_DB_URL": "postgresql://postgres:postgres@localhost:54322/postgres",  # Local DB
            "SUPABASE_KEY": "dummy-key",
            "SUPABASE_JWT_SECRET": "test-jwt-secret",
            # OAuth configuration
            "GOOGLE_CLIENT_ID": "test-google-client-id",
            "GOOGLE_CLIENT_SECRET": "test-google-client-secret",
            "GITHUB_CLIENT_ID": "test-github-client-id",
            "GITHUB_CLIENT_SECRET": "test-github-client-secret",
            "OAUTH_REDIRECT_URL": "http://localhost:8000/api/v1/auth/callback",
        }
    )


@pytest.fixture
def mock_csrf_token():
    """Return a mock CSRF token."""
    return "test_csrf_token"


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client."""
    mock_client = MagicMock()

    # Mock auth methods
    mock_client.auth = MagicMock()
    mock_client.auth.sign_up = AsyncMock()
    mock_client.auth.sign_in_with_password = AsyncMock()
    mock_client.auth.sign_out = AsyncMock()
    mock_client.auth.reset_password_email = AsyncMock()
    mock_client.auth.get_user = AsyncMock()
    mock_client.auth.exchange_code_for_session = AsyncMock()

    # Mock successful responses
    mock_client.auth.sign_up.return_value = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "user": {
            "id": "test_user_id",
            "email": "test@example.com",
            "name": "Test User",
        },
    }

    mock_client.auth.sign_in_with_password.return_value = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "user": {
            "id": "test_user_id",
            "email": "test@example.com",
            "name": "Test User",
        },
    }

    mock_client.auth.get_user.return_value = {
        "id": "test_user_id",
        "email": "test@example.com",
        "name": "Test User",
    }

    return mock_client


@pytest.fixture
def client(mock_supabase_client):
    """Create a test client with mocked dependencies."""
    app.dependency_overrides = {}

    # Mock the get_supabase_client dependency
    async def get_mock_supabase_client():
        return mock_supabase_client

    app.dependency_overrides["get_supabase_client"] = get_mock_supabase_client

    # Create test client
    test_client = TestClient(app)

    return test_client
