"""Cache manager implementation.

This module provides a Redis-based cache manager with decorator support for easy caching
of function results.
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis-based cache manager with decorator support."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        prefix: str = "",
        default_ttl: int = 3600,
    ) -> None:
        """Initialize the cache manager.

        Args:
            host: Redis host address
            port: Redis port number
            prefix: Key prefix for namespacing
            default_ttl: Default time-to-live in seconds
        """
        self.prefix = prefix
        self.default_ttl = default_ttl
        try:
            self.redis = redis.Redis(host=host, port=port, decode_responses=True)
            logger.info("Successfully connected to Redis cache at %s:%d", host, port)
        except RedisError as e:
            logger.error("Failed to connect to Redis: %s", str(e))
            raise

    def _get_full_key(self, key: str) -> str:
        """Get the full key with prefix."""
        return f"{self.prefix}:{key}" if self.prefix else key

    def _hash_key(self, value: Any) -> str:
        """Create a hash of the value for use as a cache key.

        Args:
            value: Value to hash

        Returns:
            String hash of the value
        """
        serialized = json.dumps(value, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        try:
            full_key = self._get_full_key(key)
            value = self.redis.get(full_key)
            if value is not None:
                return json.loads(value)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.error("Error retrieving from cache: %s", str(e))
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        if ttl is None:
            ttl = self.default_ttl
        try:
            full_key = self._get_full_key(key)
            return bool(self.redis.setex(full_key, ttl, json.dumps(value)))
        except (RedisError, TypeError) as e:
            logger.error("Error setting cache value: %s", str(e))
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            full_key = self._get_full_key(key)
            return bool(self.redis.delete(full_key))
        except RedisError as e:
            logger.error("Error deleting from cache: %s", str(e))
            return False

    def cleanup(self):
        """Clean up resources."""
        try:
            self.redis.close()
            logger.info("Successfully closed Redis connection")
        except RedisError as e:
            logger.error("Error closing Redis connection: %s", str(e))

    def cache_decorator(self, key_prefix: str, ttl: int | None = None):
        """Decorator for caching function results.

        Args:
            key_prefix: Prefix for the cache key
            ttl: Time-to-live in seconds (optional)

        Returns:
            Decorated function
        """

        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Create cache key from function args
                key_parts = [key_prefix, func.__name__]
                if args:
                    key_parts.append(self._hash_key(args))
                if kwargs:
                    key_parts.append(self._hash_key(kwargs))
                cache_key = ":".join(key_parts)

                # Try to get from cache first
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    logger.debug("Cache hit for key: %s", cache_key)
                    return cached_value

                # If not in cache, compute and store
                logger.debug("Cache miss for key: %s", cache_key)
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result

            return wrapper

        return decorator
