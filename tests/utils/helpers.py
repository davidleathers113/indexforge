"""Common test helper functions."""

import json
import pickle
from typing import Any, Dict, Optional
from unittest.mock import Mock

__all__ = [
    "create_mock_redis",
    "create_mock_logger",
    "create_mock_response",
    "setup_mock_cache",
]


def create_mock_redis(
    get_return: Optional[Any] = None,
    setex_return: bool = True,
    delete_return: int = 1,
) -> Mock:
    """Create a mock Redis client with configurable returns."""
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = pickle.dumps(get_return) if get_return is not None else None
    mock_redis.setex.return_value = setex_return
    mock_redis.delete.return_value = delete_return
    return mock_redis


def create_mock_logger() -> Mock:
    """Create a mock logger with all logging methods."""
    logger = Mock()
    for level in ["debug", "info", "warning", "error", "critical"]:
        setattr(logger, level, Mock())
    return logger


def create_mock_response(
    status_code: int = 200,
    json_data: Optional[Dict[str, Any]] = None,
    text: Optional[str] = None,
) -> Mock:
    """Create a mock HTTP response."""
    response = Mock()
    response.status_code = status_code

    if json_data is not None:
        response.json.return_value = json_data
        response.text = json.dumps(json_data)
    elif text is not None:
        response.text = text
        try:
            response.json.return_value = json.loads(text)
        except json.JSONDecodeError:
            response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

    return response


def setup_mock_cache(mock_redis: Mock, key_values: Dict[str, Any]) -> None:
    """Set up a mock Redis cache with initial key-value pairs."""

    def mock_get(key: str) -> Optional[bytes]:
        return pickle.dumps(key_values[key]) if key in key_values else None

    def mock_setex(key: str, ttl: int, value: bytes) -> bool:
        key_values[key] = pickle.loads(value)
        return True

    def mock_delete(key: str) -> int:
        return 1 if key_values.pop(key, None) is not None else 0

    mock_redis.get.side_effect = mock_get
    mock_redis.setex.side_effect = mock_setex
    mock_redis.delete.side_effect = mock_delete
