"""Weaviate cache providers."""

from abc import ABC, abstractmethod
import json
from typing import Any

import aioredis
from cachetools import TTLCache


class CacheProvider(ABC):
    """Abstract base class for cache providers."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time to live in seconds
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        pass


class MemoryCache(CacheProvider):
    """In-memory cache provider using TTLCache."""

    def __init__(self, maxsize: int = 1000, ttl: int = 300):
        """Initialize memory cache.

        Args:
            maxsize: Maximum cache size
            ttl: Default time to live in seconds
        """
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        try:
            return self.cache[key]
        except KeyError:
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time to live in seconds
        """
        if ttl is not None:
            # Create new cache with custom TTL
            temp_cache = TTLCache(maxsize=1, ttl=ttl)
            temp_cache[key] = value
            self.cache[key] = value
        else:
            self.cache[key] = value

    async def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key
        """
        try:
            del self.cache[key]
        except KeyError:
            pass

    async def clear(self) -> None:
        """Clear all cached values."""
        self.cache.clear()


class RedisCache(CacheProvider):
    """Redis cache provider."""

    def __init__(self, redis: aioredis.Redis):
        """Initialize Redis cache.

        Args:
            redis: Redis client instance
        """
        self.redis = redis

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        value = await self.redis.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time to live in seconds
        """
        value_str = json.dumps(value)
        if ttl is not None:
            await self.redis.setex(key, ttl, value_str)
        else:
            await self.redis.set(key, value_str)

    async def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key
        """
        await self.redis.delete(key)

    async def clear(self) -> None:
        """Clear all cached values."""
        await self.redis.flushdb()


class NullCache(CacheProvider):
    """No-op cache provider."""

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Always returns None
        """
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time to live in seconds
        """
        pass

    async def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key
        """
        pass

    async def clear(self) -> None:
        """Clear all cached values."""
        pass
