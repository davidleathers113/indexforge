"""Core fixtures for testing.

This module provides core functionality used by other fixtures:
- Base state management
- Error handling
- Logging
"""

from .base import BaseState
from .errors import ErrorState, mock_api_error, mock_auth_error, mock_validation_error
from .logger import LoggerState, mock_logger


__all__ = [
    "BaseState",
    "ErrorState",
    "LoggerState",
    "mock_api_error",
    "mock_auth_error",
    "mock_logger",
    "mock_validation_error",
]
