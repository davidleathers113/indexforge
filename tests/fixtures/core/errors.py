"""Error fixtures for testing."""

from dataclasses import dataclass
import logging
from typing import Dict
from unittest.mock import MagicMock

import pytest

from .base import BaseState

logger = logging.getLogger(__name__)


@dataclass
class ErrorState(BaseState):
    """Error state management."""

    error_message: str = ""
    error_code: str = ""
    retry_count: int = 0
    max_retries: int = 3
    should_retry: bool = True

    def reset(self):
        """Reset state to defaults."""
        super().reset()
        self.error_message = ""
        self.error_code = ""
        self.retry_count = 0
        self.should_retry = True

    def increment_retry(self) -> bool:
        """Increment retry counter and check if should retry."""
        self.retry_count += 1
        return self.should_retry and self.retry_count < self.max_retries


class APIError(Exception):
    """Custom API error with retry support."""

    def __init__(self, message: str, code: str = "API_ERROR", *args):
        super().__init__(message, *args)
        self.code = code
        self.message = message


class NetworkError(ConnectionError):
    """Custom network error with retry support."""

    def __init__(self, message: str, code: str = "NETWORK_ERROR", *args):
        super().__init__(message, *args)
        self.code = code
        self.message = message


class TimeoutException(TimeoutError):
    """Custom timeout error with retry support."""

    def __init__(self, message: str, code: str = "TIMEOUT_ERROR", *args):
        super().__init__(message, *args)
        self.code = code
        self.message = message


class AuthError(PermissionError):
    """Custom auth error with retry support."""

    def __init__(self, message: str, code: str = "AUTH_ERROR", *args):
        super().__init__(message, *args)
        self.code = code
        self.message = message


class ValidationError(ValueError):
    """Custom validation error with details."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR", details: Dict = None, *args):
        super().__init__(message, *args)
        self.code = code
        self.message = message
        self.details = details or {}


@pytest.fixture(scope="function")
def error_state():
    """Shared error state for testing."""
    state = ErrorState()
    yield state
    state.reset()


@pytest.fixture(scope="function")
def mock_api_error(error_state):
    """Simulates API errors with retry support."""

    def create_error(message: str = "API Error", code: str = "API_ERROR"):
        error_state.error_message = message
        error_state.error_code = code
        error_state.add_error(f"{code}: {message}")
        return APIError(message, code)

    mock_error = MagicMock(side_effect=create_error)
    mock_error.get_errors = error_state.get_errors
    mock_error.reset = error_state.reset
    mock_error.should_retry = lambda: error_state.increment_retry()
    return mock_error


@pytest.fixture(scope="function")
def mock_network_error(error_state):
    """Simulates network errors with retry support."""

    def create_error(message: str = "Network Error", code: str = "NETWORK_ERROR"):
        error_state.error_message = message
        error_state.error_code = code
        error_state.add_error(f"{code}: {message}")
        return NetworkError(message, code)

    mock_error = MagicMock(side_effect=create_error)
    mock_error.get_errors = error_state.get_errors
    mock_error.reset = error_state.reset
    mock_error.should_retry = lambda: error_state.increment_retry()
    return mock_error


@pytest.fixture(scope="function")
def mock_timeout_error(error_state):
    """Simulates timeout errors with retry support."""

    def create_error(message: str = "Operation timed out", code: str = "TIMEOUT_ERROR"):
        error_state.error_message = message
        error_state.error_code = code
        error_state.add_error(f"{code}: {message}")
        return TimeoutException(message, code)

    mock_error = MagicMock(side_effect=create_error)
    mock_error.get_errors = error_state.get_errors
    mock_error.reset = error_state.reset
    mock_error.should_retry = lambda: error_state.increment_retry()
    return mock_error


@pytest.fixture(scope="function")
def mock_auth_error(error_state):
    """Simulates authentication errors with retry support."""

    def create_error(message: str = "Authentication failed", code: str = "AUTH_ERROR"):
        error_state.error_message = message
        error_state.error_code = code
        error_state.add_error(f"{code}: {message}")
        return AuthError(message, code)

    mock_error = MagicMock(side_effect=create_error)
    mock_error.get_errors = error_state.get_errors
    mock_error.reset = error_state.reset
    mock_error.should_retry = lambda: error_state.increment_retry()
    return mock_error


@pytest.fixture(scope="function")
def mock_validation_error(error_state):
    """Simulates data validation errors with details."""

    def create_error(
        message: str = "Invalid data format", code: str = "VALIDATION_ERROR", details: Dict = None
    ):
        error_state.error_message = message
        error_state.error_code = code
        error_state.add_error(f"{code}: {message}")
        return ValidationError(message, code, details)

    mock_error = MagicMock(side_effect=create_error)
    mock_error.get_errors = error_state.get_errors
    mock_error.reset = error_state.reset
    mock_error.should_retry = lambda: error_state.increment_retry()
    return mock_error
