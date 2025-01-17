"""Document lineage caching for IndexForge.

This module provides caching functionality for document lineage data,
including Redis-based caching with TTL support, memory limits,
and cache invalidation strategies.
"""

import asyncio
import json
from typing import Protocol, TypeVar
from uuid import UUID

from pydantic import BaseModel
import redis.asyncio as redis

from src.core.lineage.base import DocumentLineage


T = TypeVar("T", bound=BaseModel)


class CacheConfig(BaseModel):
    """Configuration for lineage cache."""

    ttl: int = 3600  # Cache TTL in seconds
    max_memory_mb: int = 512  # Maximum memory usage in MB
    namespace: str = "lineage"  # Cache key namespace
    connection_url: str = "redis://localhost:6379/0"  # Redis connection URL


class CacheBackend(Protocol):
    """Protocol for lineage cache backends."""

    async def get(self, key: str) -> bytes | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        ...

    async def set(
        self,
        key: str,
        value: bytes,
        ttl: int | None = None,
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL in seconds
        """
        ...

    async def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key to delete
        """
        ...

    async def clear(self) -> None:
        """Clear all cached values."""
        ...


class RedisCache(CacheBackend):
    """Redis-based cache implementation."""

    def __init__(self, config: CacheConfig):
        """Initialize Redis cache.

        Args:
            config: Cache configuration
        """
        self.config = config
        self._redis: redis.Redis | None = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> redis.Redis:
        """Get Redis client, creating if needed.

        Returns:
            Redis client instance
        """
        if self._redis is None:
            async with self._lock:
                if self._redis is None:
                    self._redis = redis.from_url(
                        self.config.connection_url,
                        encoding="utf-8",
                        decode_responses=False,
                    )
                    # Configure memory limits
                    await self._redis.config_set(
                        "maxmemory",
                        str(self.config.max_memory_mb * 1024 * 1024),
                    )
                    await self._redis.config_set(
                        "maxmemory-policy",
                        "allkeys-lru",  # Least Recently Used eviction
                    )
        return self._redis

    def _make_key(self, key: str) -> str:
        """Create namespaced cache key.

        Args:
            key: Original key

        Returns:
            Namespaced key
        """
        return f"{self.config.namespace}:{key}"

    async def get(self, key: str) -> bytes | None:
        """Get value from Redis cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        client = await self._get_client()
        return await client.get(self._make_key(key))

    async def set(
        self,
        key: str,
        value: bytes,
        ttl: int | None = None,
    ) -> None:
        """Set value in Redis cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL in seconds (defaults to config TTL)
        """
        client = await self._get_client()
        await client.set(
            self._make_key(key),
            value,
            ex=ttl or self.config.ttl,
        )

    async def delete(self, key: str) -> None:
        """Delete value from Redis cache.

        Args:
            key: Cache key to delete
        """
        client = await self._get_client()
        await client.delete(self._make_key(key))

    async def clear(self) -> None:
        """Clear all cached values in namespace."""
        client = await self._get_client()
        # Get all keys in namespace
        pattern = f"{self.config.namespace}:*"
        cursor = 0
        while True:
            cursor, keys = await client.scan(
                cursor,
                match=pattern,
                count=100,
            )
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break


class LineageCache:
    """Cache manager for document lineage data."""

    def __init__(
        self,
        backend: CacheBackend | None = None,
        config: CacheConfig | None = None,
    ):
        """Initialize lineage cache.

        Args:
            backend: Optional cache backend (defaults to Redis)
            config: Optional cache configuration
        """
        self.config = config or CacheConfig()
        self._backend = backend or RedisCache(self.config)
        self._pending_invalidations: set[UUID] = set()
        self._lock = asyncio.Lock()

    def _serialize_lineage(self, lineage: DocumentLineage) -> bytes:
        """Serialize lineage data for caching.

        Args:
            lineage: Document lineage to serialize

        Returns:
            Serialized lineage data
        """
        return json.dumps(lineage.dict()).encode("utf-8")

    def _deserialize_lineage(self, data: bytes) -> DocumentLineage:
        """Deserialize cached lineage data.

        Args:
            data: Serialized lineage data

        Returns:
            Deserialized document lineage
        """
        return DocumentLineage.parse_obj(json.loads(data.decode("utf-8")))

    async def get_lineage(self, document_id: UUID) -> DocumentLineage | None:
        """Get document lineage from cache.

        Args:
            document_id: Document ID to get lineage for

        Returns:
            Cached lineage if found, None otherwise
        """
        if document_id in self._pending_invalidations:
            return None

        data = await self._backend.get(str(document_id))
        if data:
            try:
                return self._deserialize_lineage(data)
            except Exception:
                # Invalid cache data, remove it
                await self._backend.delete(str(document_id))
        return None

    async def set_lineage(
        self,
        lineage: DocumentLineage,
        ttl: int | None = None,
    ) -> None:
        """Cache document lineage.

        Args:
            lineage: Document lineage to cache
            ttl: Optional TTL override
        """
        if lineage.document_id in self._pending_invalidations:
            return

        data = self._serialize_lineage(lineage)
        await self._backend.set(str(lineage.document_id), data, ttl)

    async def invalidate_lineage(self, document_id: UUID) -> None:
        """Invalidate cached lineage for a document.

        Args:
            document_id: Document ID to invalidate
        """
        async with self._lock:
            self._pending_invalidations.add(document_id)
            await self._backend.delete(str(document_id))

    async def invalidate_related(
        self,
        document_id: UUID,
        related_ids: set[UUID],
    ) -> None:
        """Invalidate cached lineage for related documents.

        Args:
            document_id: Main document ID
            related_ids: Set of related document IDs
        """
        async with self._lock:
            self._pending_invalidations.update(related_ids)
            self._pending_invalidations.add(document_id)
            # Delete all related documents from cache
            for doc_id in related_ids | {document_id}:
                await self._backend.delete(str(doc_id))

    async def clear_pending_invalidations(self) -> None:
        """Clear set of pending invalidations."""
        async with self._lock:
            self._pending_invalidations.clear()

    async def clear(self) -> None:
        """Clear all cached lineage data."""
        await self._backend.clear()
        await self.clear_pending_invalidations()
