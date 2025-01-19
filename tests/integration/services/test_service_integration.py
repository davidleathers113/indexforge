"""Integration tests for service interactions."""

import asyncio
from typing import Any

import numpy as np
import pytest

from src.core.errors import ServiceError
from src.core.settings import Settings
from src.services import RedisService, WeaviateClient
from src.services.factory import ServiceFactory


@pytest.fixture
async def settings() -> Settings:
    """Create test settings."""
    return Settings(
        redis_url="redis://localhost:6379/0",
        redis_pool_size=5,
        weaviate_url="http://localhost:8080",
        weaviate_api_key="",
    )


@pytest.fixture
async def redis_service(settings: Settings) -> RedisService:
    """Create and initialize Redis service."""
    service = await ServiceFactory.create_cache_service(settings)
    try:
        yield service
    finally:
        await service.cleanup()


@pytest.fixture
async def weaviate_service(settings: Settings) -> WeaviateClient:
    """Create and initialize Weaviate service."""
    service = await ServiceFactory.create_vector_service(settings)
    try:
        yield service
    finally:
        await service.cleanup()


class TestServiceIntegration:
    """Test service integration scenarios."""

    @pytest.mark.asyncio
    async def test_redis_pipeline_operations(self, redis_service: RedisService):
        """Test Redis pipeline operations."""
        # Setup test data
        operations = [
            ("set", "key1", ["value1"]),
            ("set", "key2", ["value2"]),
            ("set", "key3", ["value3"]),
        ]

        # Execute pipeline
        results = await redis_service.pipeline_execute(operations)
        assert all(results), "All pipeline operations should succeed"

        # Verify results
        values = await redis_service.get_many(["key1", "key2", "key3"])
        assert values["key1"] == "value1"
        assert values["key2"] == "value2"
        assert values["key3"] == "value3"

    @pytest.mark.asyncio
    async def test_redis_complex_data_types(self, redis_service: RedisService):
        """Test Redis handling of complex data types."""
        test_data = {
            "list_key": [1, 2, 3, 4, 5],
            "dict_key": {"name": "test", "value": 42},
            "str_key": "simple string",
        }

        # Set multiple values
        success = await redis_service.set_many(test_data)
        assert success, "Setting multiple values should succeed"

        # Verify each type
        list_value = await redis_service.get("list_key")
        assert isinstance(list_value, list)
        assert list_value == [1, 2, 3, 4, 5]

        dict_value = await redis_service.get("dict_key")
        assert isinstance(dict_value, dict)
        assert dict_value == {"name": "test", "value": 42}

        str_value = await redis_service.get("str_key")
        assert isinstance(str_value, str)
        assert str_value == "simple string"

    @pytest.mark.asyncio
    async def test_weaviate_batch_operations(self, weaviate_service: WeaviateClient):
        """Test Weaviate batch operations."""
        class_name = "TestClass"
        test_objects: list[dict[str, Any]] = [
            {"text": "test document 1", "category": "A"},
            {"text": "test document 2", "category": "B"},
            {"text": "test document 3", "category": "C"},
        ]

        # Generate random vectors
        vectors = [np.random.rand(128).tolist() for _ in range(len(test_objects))]

        # Add objects in batch
        uuids = await weaviate_service.batch_add_objects(
            class_name=class_name,
            objects=test_objects,
            vectors=vectors,
        )
        assert len(uuids) == len(test_objects), "All objects should be created"

        try:
            # Verify objects were created
            for i, uuid in enumerate(uuids):
                obj = await weaviate_service.get_object(class_name, uuid)
                assert obj is not None
                assert obj["text"] == test_objects[i]["text"]
                assert obj["category"] == test_objects[i]["category"]

            # Test vector search
            search_results = await weaviate_service.search_vectors(
                class_name=class_name,
                vector=vectors[0],
                limit=2,
            )
            assert len(search_results) > 0, "Should find similar vectors"

        finally:
            # Cleanup
            await weaviate_service.delete_batch(class_name, uuids)

    @pytest.mark.asyncio
    async def test_service_error_handling(
        self, redis_service: RedisService, weaviate_service: WeaviateClient
    ):
        """Test error handling across services."""
        # Test Redis error handling
        with pytest.raises(ServiceError):
            await redis_service.pipeline_execute(
                [("invalid", "key", ["value"])],
                raise_on_error=True,
            )

        # Test Weaviate error handling
        with pytest.raises(ServiceError):
            await weaviate_service.add_object(
                class_name="NonExistentClass",
                data_object={"test": "value"},
            )

    @pytest.mark.asyncio
    async def test_service_cleanup(
        self, redis_service: RedisService, weaviate_service: WeaviateClient
    ):
        """Test proper service cleanup."""
        # Add test data
        await redis_service.set("test_key", "test_value")
        assert await redis_service.get("test_key") == "test_value"

        # Cleanup services
        await redis_service.cleanup()
        await weaviate_service.cleanup()

        # Verify services are properly cleaned up
        assert not redis_service.is_initialized
        assert not weaviate_service.is_initialized

        # Verify operations fail after cleanup
        with pytest.raises(ServiceError):
            await redis_service.get("test_key")

        with pytest.raises(ServiceError):
            await weaviate_service.health_check()

    @pytest.mark.asyncio
    async def test_service_health_monitoring(
        self, redis_service: RedisService, weaviate_service: WeaviateClient
    ):
        """Test service health monitoring."""
        # Initial health check
        assert await redis_service.health_check(), "Redis should be healthy"
        assert await weaviate_service.health_check(), "Weaviate should be healthy"

        # Verify metadata
        redis_metadata = redis_service.metadata
        assert "redis_url" in redis_metadata
        assert "pool_size" in redis_metadata

        weaviate_metadata = weaviate_service.metadata
        assert "weaviate_url" in weaviate_metadata
        assert "has_api_key" in weaviate_metadata

        # Test after operations
        await redis_service.set("test_key", "test_value")
        assert await redis_service.health_check(), "Redis should remain healthy after operations"

        await weaviate_service.add_object("TestClass", {"test": "value"})
        assert (
            await weaviate_service.health_check()
        ), "Weaviate should remain healthy after operations"

    @pytest.mark.asyncio
    async def test_concurrent_operations(
        self, redis_service: RedisService, weaviate_service: WeaviateClient
    ):
        """Test concurrent operations across services."""
        # Setup test data
        num_operations = 100
        keys = [f"key_{i}" for i in range(num_operations)]
        values = [f"value_{i}" for i in range(num_operations)]

        # Test concurrent Redis operations
        async def redis_operation(key: str, value: str):
            await redis_service.set(key, value)
            result = await redis_service.get(key)
            assert result == value

        redis_tasks = [redis_operation(k, v) for k, v in zip(keys, values, strict=False)]
        await asyncio.gather(*redis_tasks)

        # Test concurrent Weaviate operations
        vectors = [np.random.rand(128).tolist() for _ in range(num_operations)]
        objects = [{"text": f"doc_{i}", "value": i} for i in range(num_operations)]

        async def weaviate_operation(obj: dict[str, Any], vector: list[float]):
            uuid = await weaviate_service.add_object("TestClass", obj, vector)
            assert uuid is not None
            return uuid

        weaviate_tasks = [weaviate_operation(obj, vec) for obj, vec in zip(objects, vectors, strict=False)]
        uuids = await asyncio.gather(*weaviate_tasks)

        # Cleanup
        await weaviate_service.delete_batch("TestClass", uuids)

    @pytest.mark.asyncio
    async def test_metrics_collection(
        self, redis_service: RedisService, weaviate_service: WeaviateClient
    ):
        """Test service metrics collection."""
        # Get initial metrics
        redis_metrics = redis_service.get_metrics()
        weaviate_metrics = weaviate_service.get_metrics()

        assert "operations" in redis_metrics
        assert "memory_usage" in redis_metrics
        assert "error_rate" in redis_metrics

        assert "operations" in weaviate_metrics
        assert "batch_operations" in weaviate_metrics
        assert "vector_operations" in weaviate_metrics

        # Perform operations to generate metrics
        for i in range(10):
            await redis_service.set(f"key_{i}", f"value_{i}")
            await weaviate_service.add_object(
                "TestClass", {"text": f"doc_{i}"}, np.random.rand(128).tolist()
            )

        # Get updated metrics
        updated_redis_metrics = redis_service.get_metrics()
        updated_weaviate_metrics = weaviate_service.get_metrics()

        # Verify metrics were updated
        assert updated_redis_metrics["operations"] > redis_metrics["operations"]
        assert updated_weaviate_metrics["operations"] > weaviate_metrics["operations"]

        # Verify performance metrics
        assert "avg_operation_time" in updated_redis_metrics
        assert "avg_operation_time" in updated_weaviate_metrics

        # Verify error tracking
        assert "error_count" in updated_redis_metrics
        assert "error_count" in updated_weaviate_metrics

    @pytest.mark.asyncio
    async def test_error_recovery(
        self, redis_service: RedisService, weaviate_service: WeaviateClient
    ):
        """Test service error recovery scenarios."""
        # Test Redis recovery
        await redis_service.set("test_key", "test_value")

        # Simulate connection error
        redis_service._client = None  # Force connection loss

        # Operation should fail
        with pytest.raises(ServiceError):
            await redis_service.get("test_key")

        # Service should recover on next operation
        await redis_service.initialize()
        result = await redis_service.get("test_key")
        assert result == "test_value"

        # Test Weaviate recovery
        vector = np.random.rand(128).tolist()
        uuid = await weaviate_service.add_object("TestClass", {"text": "test_doc"}, vector)

        # Simulate connection error
        weaviate_service._client = None  # Force connection loss

        # Operation should fail
        with pytest.raises(ServiceError):
            await weaviate_service.get_object("TestClass", uuid)

        # Service should recover on next operation
        await weaviate_service.initialize()
        obj = await weaviate_service.get_object("TestClass", uuid)
        assert obj is not None
        assert obj["text"] == "test_doc"

        # Cleanup
        await weaviate_service.delete_object("TestClass", uuid)

    @pytest.mark.asyncio
    async def test_resource_management(
        self, redis_service: RedisService, weaviate_service: WeaviateClient
    ):
        """Test service resource management."""
        # Monitor Redis connection pool
        initial_pool_size = len(redis_service._pool)

        # Execute multiple concurrent operations
        async def redis_operation(i: int):
            await redis_service.set(f"key_{i}", f"value_{i}")
            await asyncio.sleep(0.1)  # Simulate work
            await redis_service.get(f"key_{i}")

        tasks = [redis_operation(i) for i in range(20)]
        await asyncio.gather(*tasks)

        # Verify pool size hasn't grown
        assert len(redis_service._pool) <= initial_pool_size

        # Monitor Weaviate batch operations
        batch_metrics = []
        for batch_size in [10, 50, 100]:
            vectors = [np.random.rand(128).tolist() for _ in range(batch_size)]
            objects = [{"text": f"doc_{i}"} for i in range(batch_size)]

            start_memory = weaviate_service.get_metrics()["memory_usage"]
            uuids = await weaviate_service.batch_add_objects("TestClass", objects, vectors)
            end_memory = weaviate_service.get_metrics()["memory_usage"]

            batch_metrics.append(
                {"batch_size": batch_size, "memory_impact": end_memory - start_memory}
            )

            # Cleanup
            await weaviate_service.delete_batch("TestClass", uuids)

        # Verify memory usage scales reasonably with batch size
        memory_ratios = [m["memory_impact"] / m["batch_size"] for m in batch_metrics]
        avg_ratio = sum(memory_ratios) / len(memory_ratios)
        assert all(
            0.5 <= ratio / avg_ratio <= 2.0 for ratio in memory_ratios
        ), "Memory usage should scale linearly with batch size"
