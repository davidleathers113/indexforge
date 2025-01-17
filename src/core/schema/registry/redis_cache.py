"""Redis-based schema cache implementation.

This module provides a Redis-backed caching layer for schema definitions,
supporting distributed caching with TTL and size limits.
"""

import json
from typing import Optional

from redis.asyncio import Redis

from src.core.schema.registry.cache import CacheConfig, SchemaCache
from src.core.schema.schema import Schema


class RedisSchemaCache(SchemaCache):
    """Redis-backed schema cache implementation."""

    def __init__(
        self,
        redis: Redis,
        config: Optional[CacheConfig] = None,
    ) -> None:
        """Initialize Redis schema cache.

        Args:
            redis: Redis client instance
            config: Optional cache configuration
        """
        super().__init__(config)
        self.redis = redis

    async def get(self, key: str) -> Optional[Schema]:
        """Get schema from Redis cache.

        Args:
            key: Cache key (schema name)

        Returns:
            Cached schema if found and valid, None otherwise
        """
        cache_key = self._get_cache_key(key)
        data = await self.redis.get(cache_key)
        if not data:
            return None

        try:
            schema_dict = json.loads(data)
            return Schema.from_dict(schema_dict)
        except Exception:
            # Invalid cache data, remove it
            await self.delete(key)
            return None

    async def set(self, key: str, schema: Schema) -> None:
        """Store schema in Redis cache.

        Args:
            key: Cache key (schema name)
            schema: Schema to cache
        """
        cache_key = self._get_cache_key(key)
        schema_json = json.dumps(schema.to_dict())

        # Use pipeline for atomic operations
        async with self.redis.pipeline() as pipe:
            # Add to cache with TTL if configured
            if self.config.ttl:
                await pipe.setex(cache_key, self.config.ttl, schema_json)
            else:
                await pipe.set(cache_key, schema_json)

            # Maintain size limit if configured
            if self.config.max_size:
                await pipe.zcard(self._size_key)
                await pipe.zadd(self._size_key, {key: self._current_timestamp()})

                # Trim if needed
                size = await pipe.zcard(self._size_key)
                if size > self.config.max_size:
                    # Remove oldest entries
                    to_remove = size - self.config.max_size
                    old_keys = await pipe.zrange(self._size_key, 0, to_remove - 1)
                    if old_keys:
                        await pipe.delete(*[self._get_cache_key(k) for k in old_keys])
                        await pipe.zrem(self._size_key, *old_keys)

            await pipe.execute()

    async def delete(self, key: str) -> None:
        """Remove schema from Redis cache.

        Args:
            key: Cache key (schema name)
        """
        cache_key = self._get_cache_key(key)
        async with self.redis.pipeline() as pipe:
            await pipe.delete(cache_key)
            await pipe.zrem(self._size_key, key)
            await pipe.execute()

    async def clear(self) -> None:
        """Clear all cached schemas."""
        # Get all cache keys
        keys = await self.redis.zrange(self._size_key, 0, -1)
        if keys:
            # Delete all schema entries and size tracking
            async with self.redis.pipeline() as pipe:
                await pipe.delete(*[self._get_cache_key(k) for k in keys])
                await pipe.delete(self._size_key)
                await pipe.execute()

    def _get_cache_key(self, key: str) -> str:
        """Get Redis key for schema cache entry.

        Args:
            key: Schema name

        Returns:
            Redis cache key
        """
        return f"{self.config.namespace}:schema:{key}"

    @property
    def _size_key(self) -> str:
        """Get Redis key for cache size tracking."""
        return f"{self.config.namespace}:size"

    def _current_timestamp(self) -> float:
        """Get current timestamp for cache entry scoring."""
        import time

        return time.time()
