"""Weaviate cache strategies."""

from abc import ABC, abstractmethod
from typing import Any

from src.api.repositories.weaviate.cache.providers import CacheProvider


class CacheStrategy(ABC):
    """Abstract base class for cache strategies."""

    def __init__(self, provider: CacheProvider):
        """Initialize cache strategy.

        Args:
            provider: Cache provider implementation
        """
        self.provider = provider

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


class SimpleCache(CacheStrategy):
    """Simple cache strategy with basic operations."""

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        return await self.provider.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time to live in seconds
        """
        await self.provider.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key
        """
        await self.provider.delete(key)

    async def clear(self) -> None:
        """Clear all cached values."""
        await self.provider.clear()


class TwoLevelCache(CacheStrategy):
    """Two-level cache strategy with local and remote caches."""

    def __init__(self, local_provider: CacheProvider, remote_provider: CacheProvider):
        """Initialize two-level cache.

        Args:
            local_provider: Local cache provider
            remote_provider: Remote cache provider
        """
        self.local = local_provider
        self.remote = remote_provider

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        # Try local cache first
        value = await self.local.get(key)
        if value is not None:
            return value

        # Try remote cache
        value = await self.remote.get(key)
        if value is not None:
            # Update local cache
            await self.local.set(key, value)
            return value

        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time to live in seconds
        """
        # Set in both caches
        await self.local.set(key, value, ttl)
        await self.remote.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key
        """
        # Delete from both caches
        await self.local.delete(key)
        await self.remote.delete(key)

    async def clear(self) -> None:
        """Clear all cached values."""
        # Clear both caches
        await self.local.clear()
        await self.remote.clear()


class QueryCache(CacheStrategy):
    """Cache strategy optimized for query results."""

    def __init__(self, provider: CacheProvider, namespace: str = "query"):
        """Initialize query cache.

        Args:
            provider: Cache provider implementation
            namespace: Cache namespace
        """
        super().__init__(provider)
        self.namespace = namespace

    def _make_key(self, query_hash: str) -> str:
        """Create cache key for query.

        Args:
            query_hash: Query hash

        Returns:
            Cache key
        """
        return f"{self.namespace}:{query_hash}"

    async def get_query_result(
        self, query_hash: str, metadata: dict | None = None
    ) -> dict | None:
        """Get cached query result.

        Args:
            query_hash: Query hash
            metadata: Optional query metadata

        Returns:
            Cached result if found, None otherwise
        """
        key = self._make_key(query_hash)
        result = await self.get(key)

        if result and metadata:
            # Validate metadata matches
            cached_metadata = result.get("metadata", {})
            if cached_metadata != metadata:
                return None

        return result

    async def set_query_result(
        self,
        query_hash: str,
        result: dict,
        metadata: dict | None = None,
        ttl: int | None = None,
    ) -> None:
        """Cache query result.

        Args:
            query_hash: Query hash
            result: Query result
            metadata: Optional query metadata
            ttl: Optional time to live in seconds
        """
        key = self._make_key(query_hash)
        if metadata:
            result["metadata"] = metadata
        await self.set(key, result, ttl)

    async def invalidate_query(self, query_hash: str) -> None:
        """Invalidate cached query result.

        Args:
            query_hash: Query hash
        """
        key = self._make_key(query_hash)
        await self.delete(key)
