"""Test configuration for auth routes."""

from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from src.api.config import Settings
from src.api.dependencies.supabase import get_supabase_client
from src.api.routers.auth import router as auth_router


@pytest.fixture
def app(mock_supabase_client) -> FastAPI:
    """Create a test FastAPI application."""
    app = FastAPI()
    app.include_router(auth_router)

    # Override Supabase client dependency
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_client

    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_settings() -> Settings:
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


@pytest.fixture
def mock_supabase_client() -> AsyncMock:
    """Create a mock Supabase client."""
    mock = AsyncMock()
    mock.auth = AsyncMock()

    # Mock user data
    mock_user = MagicMock(
        id="test_user_id",
        email="test@example.com",
        user_metadata={"name": "Test User"},
        created_at="2024-01-01T00:00:00",
    )

    # Mock session data
    mock_session = MagicMock(
        access_token="test_access_token",
        refresh_token="test_refresh_token",
    )

    # Mock auth responses
    mock.auth.sign_up.return_value = MagicMock(user=mock_user, session=mock_session)
    mock.auth.sign_in_with_password.return_value = MagicMock(user=mock_user, session=mock_session)
    mock.auth.sign_in_with_oauth.return_value = MagicMock(user=mock_user, session=mock_session)
    mock.auth.get_user.return_value = MagicMock(user=mock_user)
    mock.auth.refresh_session.return_value = MagicMock(user=mock_user, session=mock_session)

    return mock


@pytest.fixture
def mock_csrf_token() -> str:
    """Create a mock CSRF token."""
    return "test_csrf_token"


@pytest.fixture
def mock_oauth_state() -> str:
    """Create a mock OAuth state token."""
    return "test_oauth_state"
