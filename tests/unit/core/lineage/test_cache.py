"""Unit tests for document lineage caching."""

import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.core.lineage.base import DocumentLineage, SourceInfo
from src.core.lineage.cache import CacheBackend, CacheConfig, LineageCache, RedisCache


@pytest.fixture
def config():
    """Create test cache configuration."""
    return CacheConfig(
        ttl=60,
        max_memory_mb=128,
        namespace="test",
        connection_url="redis://localhost:6379/1",
    )


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    mock.scan = AsyncMock(return_value=(0, []))
    mock.config_set = AsyncMock()
    return mock


@pytest.fixture
def mock_backend():
    """Create mock cache backend."""
    mock = AsyncMock(spec=CacheBackend)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    mock.clear = AsyncMock()
    return mock


@pytest.fixture
def test_lineage():
    """Create test document lineage."""
    return DocumentLineage(
        document_id=uuid4(),
        current_version=1,
        source_info=SourceInfo(
            source_id="test",
            source_type="test",
            location="/test",
        ),
    )


@pytest.mark.asyncio
async def test_redis_cache_initialization(config, mock_redis):
    """Test Redis cache initialization."""
    with patch("redis.asyncio.from_url", return_value=mock_redis):
        cache = RedisCache(config)
        client = await cache._get_client()

        assert client == mock_redis
        mock_redis.config_set.assert_any_call(
            "maxmemory",
            str(config.max_memory_mb * 1024 * 1024),
        )
        mock_redis.config_set.assert_any_call(
            "maxmemory-policy",
            "allkeys-lru",
        )


@pytest.mark.asyncio
async def test_redis_cache_operations(config, mock_redis):
    """Test Redis cache operations."""
    with patch("redis.asyncio.from_url", return_value=mock_redis):
        cache = RedisCache(config)

        # Test get
        mock_redis.get.return_value = b"test"
        result = await cache.get("key")
        assert result == b"test"
        mock_redis.get.assert_called_with(f"{config.namespace}:key")

        # Test set
        await cache.set("key", b"value", ttl=30)
        mock_redis.set.assert_called_with(
            f"{config.namespace}:key",
            b"value",
            ex=30,
        )

        # Test delete
        await cache.delete("key")
        mock_redis.delete.assert_called_with(f"{config.namespace}:key")

        # Test clear
        mock_redis.scan.side_effect = [(1, ["key1", "key2"]), (0, ["key3"])]
        await cache.clear()
        mock_redis.delete.assert_any_call("key1", "key2")
        mock_redis.delete.assert_any_call("key3")


@pytest.mark.asyncio
async def test_lineage_cache_get(mock_backend, test_lineage):
    """Test lineage cache get operations."""
    cache = LineageCache(backend=mock_backend)

    # Test cache miss
    result = await cache.get_lineage(test_lineage.document_id)
    assert result is None
    mock_backend.get.assert_called_with(str(test_lineage.document_id))

    # Test cache hit
    mock_backend.get.return_value = json.dumps(test_lineage.dict()).encode("utf-8")
    result = await cache.get_lineage(test_lineage.document_id)
    assert result == test_lineage

    # Test invalid cache data
    mock_backend.get.return_value = b"invalid"
    result = await cache.get_lineage(test_lineage.document_id)
    assert result is None
    mock_backend.delete.assert_called_with(str(test_lineage.document_id))


@pytest.mark.asyncio
async def test_lineage_cache_set(mock_backend, test_lineage):
    """Test lineage cache set operations."""
    cache = LineageCache(backend=mock_backend)

    # Test normal set
    await cache.set_lineage(test_lineage)
    mock_backend.set.assert_called_with(
        str(test_lineage.document_id),
        json.dumps(test_lineage.dict()).encode("utf-8"),
        None,
    )

    # Test set with TTL
    await cache.set_lineage(test_lineage, ttl=30)
    mock_backend.set.assert_called_with(
        str(test_lineage.document_id),
        json.dumps(test_lineage.dict()).encode("utf-8"),
        30,
    )

    # Test set with pending invalidation
    await cache.invalidate_lineage(test_lineage.document_id)
    await cache.set_lineage(test_lineage)
    assert len(mock_backend.set.mock_calls) == 2  # No new calls


@pytest.mark.asyncio
async def test_lineage_cache_invalidation(mock_backend, test_lineage):
    """Test lineage cache invalidation."""
    cache = LineageCache(backend=mock_backend)

    # Test single invalidation
    await cache.invalidate_lineage(test_lineage.document_id)
    mock_backend.delete.assert_called_with(str(test_lineage.document_id))
    assert test_lineage.document_id in cache._pending_invalidations

    # Test related invalidation
    related_ids = {uuid4(), uuid4()}
    await cache.invalidate_related(test_lineage.document_id, related_ids)
    for doc_id in related_ids | {test_lineage.document_id}:
        mock_backend.delete.assert_any_call(str(doc_id))
        assert doc_id in cache._pending_invalidations

    # Test clear pending
    await cache.clear_pending_invalidations()
    assert len(cache._pending_invalidations) == 0


@pytest.mark.asyncio
async def test_lineage_cache_clear(mock_backend):
    """Test lineage cache clear."""
    cache = LineageCache(backend=mock_backend)

    # Add some pending invalidations
    doc_ids = {uuid4(), uuid4()}
    for doc_id in doc_ids:
        await cache.invalidate_lineage(doc_id)

    # Clear cache
    await cache.clear()
    mock_backend.clear.assert_called_once()
    assert len(cache._pending_invalidations) == 0
