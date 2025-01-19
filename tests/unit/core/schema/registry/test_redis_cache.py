"""Unit tests for Redis-based schema cache implementation."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.schema.base import SchemaType, SchemaVersion
from src.core.schema.registry.cache import CacheConfig
from src.core.schema.registry.redis_cache import RedisSchemaCache
from src.core.schema.schema import FieldDefinition, Schema


@pytest.fixture
def redis_mock():
    """Create Redis client mock."""
    redis = AsyncMock()
    redis.pipeline = MagicMock()
    return redis


@pytest.fixture
def cache_config():
    """Create cache configuration."""
    return CacheConfig(ttl=60, max_size=2, namespace="test")


@pytest.fixture
def redis_cache(redis_mock, cache_config):
    """Create Redis cache instance."""
    return RedisSchemaCache(redis=redis_mock, config=cache_config)


@pytest.fixture
def test_schema():
    """Create test schema."""
    return Schema(
        name="test_schema",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "title": FieldDefinition(type="string", required=True),
        },
        required_fields={"title"},
        description="Test schema",
    )


@pytest.mark.asyncio
async def test_get_schema_not_found(redis_cache, redis_mock):
    """Test getting non-existent schema from cache."""
    redis_mock.get.return_value = None
    schema = await redis_cache.get("nonexistent")
    assert schema is None
    redis_mock.get.assert_called_once_with("test:schema:nonexistent")


@pytest.mark.asyncio
async def test_get_schema_success(redis_cache, redis_mock, test_schema):
    """Test getting existing schema from cache."""
    # Setup mock
    schema_json = json.dumps(test_schema.to_dict())
    redis_mock.get.return_value = schema_json

    # Get schema
    schema = await redis_cache.get("test_schema")
    assert schema is not None
    assert schema.name == test_schema.name
    assert schema.version == test_schema.version
    redis_mock.get.assert_called_once_with("test:schema:test_schema")


@pytest.mark.asyncio
async def test_get_schema_invalid_data(redis_cache, redis_mock):
    """Test handling invalid cache data."""
    # Setup mock with invalid JSON
    redis_mock.get.return_value = "invalid json"

    # Get schema should handle error and return None
    schema = await redis_cache.get("test_schema")
    assert schema is None

    # Should attempt to delete invalid data
    redis_mock.pipeline.assert_called_once()


@pytest.mark.asyncio
async def test_set_schema(redis_cache, redis_mock, test_schema):
    """Test storing schema in cache."""
    # Setup pipeline mock
    pipe = AsyncMock()
    redis_mock.pipeline.return_value.__aenter__.return_value = pipe
    pipe.zcard.return_value = 1

    # Store schema
    await redis_cache.set("test_schema", test_schema)

    # Verify Redis operations
    pipe.setex.assert_called_once()
    pipe.zadd.assert_called_once()
    pipe.execute.assert_called_once()


@pytest.mark.asyncio
async def test_set_schema_size_limit(redis_cache, redis_mock, test_schema):
    """Test cache size limit enforcement."""
    # Setup pipeline mock
    pipe = AsyncMock()
    redis_mock.pipeline.return_value.__aenter__.return_value = pipe
    pipe.zcard.return_value = 3  # Over size limit
    pipe.zrange.return_value = ["old_key"]

    # Store schema
    await redis_cache.set("test_schema", test_schema)

    # Verify Redis operations
    pipe.zrange.assert_called_once()  # Should get old keys
    pipe.delete.assert_called_once()  # Should delete old entries
    pipe.zrem.assert_called_once()  # Should remove from size tracking


@pytest.mark.asyncio
async def test_delete_schema(redis_cache, redis_mock):
    """Test deleting schema from cache."""
    # Setup pipeline mock
    pipe = AsyncMock()
    redis_mock.pipeline.return_value.__aenter__.return_value = pipe

    # Delete schema
    await redis_cache.delete("test_schema")

    # Verify Redis operations
    pipe.delete.assert_called_once_with("test:schema:test_schema")
    pipe.zrem.assert_called_once_with("test:size", "test_schema")
    pipe.execute.assert_called_once()


@pytest.mark.asyncio
async def test_clear_cache(redis_cache, redis_mock):
    """Test clearing entire cache."""
    # Setup pipeline mock
    pipe = AsyncMock()
    redis_mock.pipeline.return_value.__aenter__.return_value = pipe
    redis_mock.zrange.return_value = ["key1", "key2"]

    # Clear cache
    await redis_cache.clear()

    # Verify Redis operations
    redis_mock.zrange.assert_called_once_with("test:size", 0, -1)
    pipe.delete.assert_called()  # Should delete all keys
    pipe.execute.assert_called_once()
