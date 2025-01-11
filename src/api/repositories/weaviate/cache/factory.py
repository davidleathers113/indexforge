"""Weaviate cache factory."""

from functools import lru_cache
from typing import Optional

import aioredis

from src.api.config.settings import settings
from src.api.repositories.weaviate.cache.providers import (
    CacheProvider,
    MemoryCache,
    NullCache,
    RedisCache,
)
from src.api.repositories.weaviate.cache.strategy import (
    CacheStrategy,
    QueryCache,
    SimpleCache,
    TwoLevelCache,
)


@lru_cache
def get_redis_client() -> aioredis.Redis:
    """Get Redis client instance.

    Returns:
        Redis client
    """
    return aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        encoding="utf-8",
        decode_responses=True,
    )


def create_cache_provider(provider_type: str = "memory") -> CacheProvider:
    """Create cache provider instance.

    Args:
        provider_type: Type of cache provider ("memory", "redis", or "null")

    Returns:
        Cache provider instance

    Raises:
        ValueError: If provider type is invalid
    """
    if provider_type == "memory":
        return MemoryCache(
            maxsize=settings.CACHE_MAX_SIZE,
            ttl=settings.CACHE_TTL,
        )
    elif provider_type == "redis":
        redis = get_redis_client()
        return RedisCache(redis)
    elif provider_type == "null":
        return NullCache()
    else:
        raise ValueError(f"Invalid cache provider type: {provider_type}")


def create_cache_strategy(
    strategy_type: str = "simple",
    provider_type: str = "memory",
    namespace: Optional[str] = None,
) -> CacheStrategy:
    """Create cache strategy instance.

    Args:
        strategy_type: Type of cache strategy ("simple", "two_level", or "query")
        provider_type: Type of cache provider ("memory", "redis", or "null")
        namespace: Optional namespace for query cache

    Returns:
        Cache strategy instance

    Raises:
        ValueError: If strategy type is invalid
    """
    if strategy_type == "simple":
        provider = create_cache_provider(provider_type)
        return SimpleCache(provider)
    elif strategy_type == "two_level":
        local = create_cache_provider("memory")
        remote = create_cache_provider("redis")
        return TwoLevelCache(local, remote)
    elif strategy_type == "query":
        provider = create_cache_provider(provider_type)
        return QueryCache(provider, namespace=namespace or "query")
    else:
        raise ValueError(f"Invalid cache strategy type: {strategy_type}")


@lru_cache
def get_default_cache() -> CacheStrategy:
    """Get default cache strategy instance.

    Returns:
        Default cache strategy
    """
    return create_cache_strategy(
        strategy_type=settings.CACHE_STRATEGY,
        provider_type=settings.CACHE_PROVIDER,
    )
