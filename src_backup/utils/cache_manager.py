"""Cache management utilities for optimizing performance.

This module provides Redis-based caching functionality with retry mechanisms for
resilient data storage and retrieval. It includes:

1. CacheManager:
   - Redis connection management
   - Key prefixing and TTL support
   - Serialization using pickle
   - Error handling and logging
   - Automatic cleanup

2. Retry Mechanism:
   - Exponential backoff
   - Configurable retry attempts
   - Logging of retry attempts
   - Exception handling

3. Decorators:
   - @cached_with_retry: Combines caching and retry logic
   - Automatic key generation from function arguments
   - Support for complex data types
   - Configurable TTL and retry settings

Usage:
    ```python
    from src.utils.cache_manager import CacheManager, cached_with_retry

    # Basic caching
    cache = CacheManager(prefix="myapp", default_ttl=3600)
    cache.set("key", "value")
    value = cache.get("key")

    # Decorator usage
    @cached_with_retry(cache_manager=cache, key_prefix="data", max_attempts=3)
    def expensive_operation(arg1, arg2):
        # Function implementation
        return result
    ```

Note:
    - Uses pickle for serialization (supports complex Python objects)
    - Handles Redis connection failures gracefully
    - Provides automatic resource cleanup
    - Thread-safe operations
"""

from collections.abc import Callable
from functools import wraps
import hashlib
import json
import logging
import pickle
from typing import Any

import redis
from redis.exceptions import RedisError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class CacheManager:
    """Manages caching operations with Redis."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        prefix: str = "cache",
        default_ttl: int = 3600,
        logger: logging.Logger | None = None,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 2,
        retry_on_timeout: bool = True,
    ):
        self.prefix = prefix
        self.default_ttl = default_ttl
        self.logger = logger or logging.getLogger(__name__)
        try:
            self.redis = redis.Redis(
                host=host,
                port=port,
                socket_timeout=socket_timeout,
                socket_connect_timeout=socket_connect_timeout,
                retry_on_timeout=retry_on_timeout,
            )
            self.redis.ping()  # Test connection
        except RedisError as e:
            self.logger.warning(f"Failed to connect to Redis: {e!s}")
            self.redis = None

    def _get_full_key(self, key: str) -> str:
        """Get the full key with prefix."""
        return f"{self.prefix}:{key}"

    def _hash_key(self, value: Any) -> str:
        """Generate a hash for a value to use as part of a cache key."""
        if value is None:
            return "none"
        try:
            # Convert the value to a JSON string for consistent hashing
            json_str = json.dumps(value, sort_keys=True)
            return hashlib.sha256(json_str.encode()).hexdigest()
        except (TypeError, ValueError):
            # If value can't be JSON serialized, use its string representation
            return hashlib.sha256(str(value).encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """Get a value from the cache."""
        if not self.redis:
            return None
        try:
            full_key = self._get_full_key(key)
            value = self.redis.get(full_key)
            self.logger.debug(f"Got value from Redis: {value}")
            if value:
                try:
                    result = pickle.loads(value)
                    self.logger.debug(f"Unpickled value: {result}")
                    return result
                except (pickle.PickleError, TypeError, ValueError) as e:
                    self.logger.warning(f"Failed to unpickle value: {e!s}")
                    # Don't return raw bytes/invalid data
                    return None
            return None
        except Exception as e:
            self.logger.exception(f"Error getting from cache: {e!s}")
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set a value in the cache with optional TTL."""
        if not self.redis:
            return False
        try:
            full_key = self._get_full_key(key)
            serialized = pickle.dumps(value)
            if ttl is None:
                ttl = self.default_ttl
            return bool(self.redis.setex(full_key, ttl, serialized))
        except Exception as e:
            self.logger.exception(f"Error setting cache: {e!s}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.redis:
            return False
        try:
            full_key = self._get_full_key(key)
            return bool(self.redis.delete(full_key))
        except Exception as e:
            self.logger.exception(f"Error deleting from cache: {e!s}")
            return False

    def cleanup(self):
        """Clean up resources."""
        try:
            if self.redis:
                self.redis.close()
        except Exception as e:
            self.logger.exception(f"Error cleaning up cache: {e!s}")

    def cache_decorator(self, key_prefix: str, ttl: int | None = None):
        """Decorator to cache function results.

        Args:
            key_prefix: Prefix for cache key
            ttl: Optional TTL in seconds

        Returns:
            Decorated function
        """

        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from function args
                key_parts = [key_prefix, func.__name__]

                # Add args to key
                if args:
                    key_parts.extend(str(arg) for arg in args[1:])  # Skip self

                # Add sorted kwargs to key
                if kwargs:
                    sorted_items = sorted(kwargs.items())
                    key_parts.extend(f"{k}:{self._hash_key(v)}" for k, v in sorted_items)

                cache_key = ":".join(key_parts)

                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # Generate value and cache it
                value = func(*args, **kwargs)
                self.set(cache_key, value, ttl)
                return value

            return wrapper

        return decorator


def create_retry_decorator(
    max_attempts: int = 3,
    min_wait: int = 4,
    max_wait: int = 10,
    logger: logging.Logger | None = None,
):
    """Create a retry decorator with exponential backoff."""
    logger = logger or logging.getLogger(__name__)

    def log_before_retry(retry_state):
        """Log before retry attempt."""
        logger.warning(
            f"Retrying operation. Attempt {retry_state.attempt_number} of {max_attempts}"
        )

    def log_after_retry(retry_state):
        """Log after retry attempt."""
        logger.info(f"Operation succeeded after {retry_state.attempt_number} attempts")

    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=min_wait, max=max_wait),
        retry=retry_if_exception_type(Exception),
        before=log_before_retry,
        after=log_after_retry,
    )


def cached_with_retry(cache_manager: CacheManager, key_prefix: str, max_attempts: int = 3):
    """Decorator that combines caching and retry logic.

    Args:
        cache_manager: CacheManager instance
        key_prefix: Prefix for cache keys
        max_attempts: Maximum number of retry attempts

    Returns:
        Decorated function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache key
            key_parts = [key_prefix, func.__name__]
            if args:
                key_parts.extend(str(arg) for arg in args[1:])  # Skip self
            if kwargs:
                sorted_items = sorted(kwargs.items())
                key_parts.extend(f"{k}:{cache_manager._hash_key(v)}" for k, v in sorted_items)
            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Create retry decorator
            retry_decorator = create_retry_decorator(max_attempts=max_attempts)

            @retry_decorator
            def execute_with_retry():
                value = func(*args, **kwargs)
                cache_manager.set(cache_key, value)
                return value

            return execute_with_retry()

        return wrapper

    return decorator
