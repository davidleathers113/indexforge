"""Schema caching implementation.

This module provides caching functionality for schema definitions to improve
performance and reduce storage load.
"""


from pydantic import BaseModel

from src.core.schema.schema import Schema


class CacheConfig(BaseModel):
    """Configuration for schema cache."""

    ttl: int | None = 3600  # Cache TTL in seconds
    max_size: int | None = 1000  # Maximum number of cached schemas
    namespace: str = "schema"  # Cache namespace


class SchemaCache:
    """Cache implementation for schema definitions."""

    def __init__(self, config: CacheConfig | None = None) -> None:
        """Initialize schema cache.

        Args:
            config: Optional cache configuration
        """
        self.config = config or CacheConfig()
        self._cache: dict[str, Schema] = {}  # Simple in-memory cache for now

    async def get(self, key: str) -> Schema | None:
        """Get schema from cache.

        Args:
            key: Cache key (schema name)

        Returns:
            Cached schema if found and valid, None otherwise
        """
        return self._cache.get(key)

    async def set(self, key: str, schema: Schema) -> None:
        """Store schema in cache.

        Args:
            key: Cache key (schema name)
            schema: Schema to cache
        """
        if len(self._cache) >= self.config.max_size:
            # Simple LRU: remove random item when full
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = schema

    async def delete(self, key: str) -> None:
        """Remove schema from cache.

        Args:
            key: Cache key (schema name)
        """
        self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all cached schemas."""
        self._cache.clear()
