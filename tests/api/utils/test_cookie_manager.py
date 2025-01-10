"""Tests for cookie management utilities."""

import pytest
from fastapi import Response
from pydantic import HttpUrl

from src.api.utils.cookie_manager import (
    clear_auth_cookies,
    clear_oauth_cookies,
    set_auth_cookies,
    set_oauth_cookies,
)


@pytest.fixture
def mock_response():
    """Create a mock response object."""

    class MockResponse(Response):
        def __init__(self):
            self.cookies = {}
            self.deleted_cookies = set()

        def set_cookie(
            self,
            key: str,
            value: str = "",
            max_age: int = None,
            httponly: bool = False,
            secure: bool = False,
            samesite: str = None,
        ):
            """Mock set_cookie method."""
            self.cookies[key] = {
                "value": value,
                "max_age": max_age,
                "httponly": httponly,
                "secure": secure,
                "samesite": samesite,
            }

        def delete_cookie(self, key: str):
            """Mock delete_cookie method."""
            if key in self.cookies:
                del self.cookies[key]
            self.deleted_cookies.add(key)

    return MockResponse()


def test_set_auth_cookies(mock_response):
    """Test setting authentication cookies."""
    # Arrange
    access_token = "test_access_token"
    refresh_token = "test_refresh_token"
    csrf_token = "test_csrf_token"

    # Act
    set_auth_cookies(mock_response, access_token, refresh_token, csrf_token)

    # Assert
    assert mock_response.cookies["access_token"]["value"] == access_token
    assert mock_response.cookies["refresh_token"]["value"] == refresh_token
    assert mock_response.cookies["csrf_token"]["value"] == csrf_token

    # Check security settings
    for cookie in mock_response.cookies.values():
        assert cookie["httponly"] is True
        assert cookie["secure"] is True

    # Check specific settings
    assert mock_response.cookies["access_token"]["max_age"] == 3600  # 1 hour
    assert mock_response.cookies["refresh_token"]["max_age"] == 7 * 24 * 3600  # 7 days
    assert mock_response.cookies["csrf_token"]["samesite"] == "strict"


def test_set_auth_cookies_without_csrf(mock_response):
    """Test setting authentication cookies without CSRF token."""
    # Act
    set_auth_cookies(mock_response, "access", "refresh")

    # Assert
    assert "csrf_token" not in mock_response.cookies
    assert mock_response.cookies["access_token"]["value"] == "access"
    assert mock_response.cookies["refresh_token"]["value"] == "refresh"


def test_set_oauth_cookies(mock_response):
    """Test setting OAuth cookies."""
    # Arrange
    state = "test_state"
    redirect_to = HttpUrl("http://example.com/callback")

    # Act
    set_oauth_cookies(mock_response, state, redirect_to)

    # Assert
    assert mock_response.cookies["oauth_state"]["value"] == state
    assert mock_response.cookies["oauth_redirect"]["value"] == str(redirect_to)

    # Check security settings
    for cookie in mock_response.cookies.values():
        assert cookie["httponly"] is True
        assert cookie["secure"] is True
        assert cookie["max_age"] == 300  # 5 minutes
        assert cookie["samesite"] == "lax"


def test_set_oauth_cookies_without_redirect(mock_response):
    """Test setting OAuth cookies without redirect URL."""
    # Act
    set_oauth_cookies(mock_response, "state")

    # Assert
    assert "oauth_redirect" not in mock_response.cookies
    assert mock_response.cookies["oauth_state"]["value"] == "state"


def test_clear_auth_cookies(mock_response):
    """Test clearing authentication cookies."""
    # Arrange
    set_auth_cookies(mock_response, "access", "refresh", "csrf")

    # Act
    clear_auth_cookies(mock_response)

    # Assert
    assert "access_token" not in mock_response.cookies
    assert "refresh_token" not in mock_response.cookies
    assert "csrf_token" not in mock_response.cookies
    assert mock_response.deleted_cookies == {"access_token", "refresh_token", "csrf_token"}


def test_clear_oauth_cookies(mock_response):
    """Test clearing OAuth cookies."""
    # Arrange
    set_oauth_cookies(mock_response, "state", HttpUrl("http://example.com"))

    # Act
    clear_oauth_cookies(mock_response)

    # Assert
    assert "oauth_state" not in mock_response.cookies
    assert "oauth_redirect" not in mock_response.cookies
    assert mock_response.deleted_cookies == {"oauth_state", "oauth_redirect"}
