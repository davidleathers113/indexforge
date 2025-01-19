"""Integration tests for service performance benchmarks."""

import asyncio
from statistics import mean
import time

import numpy as np
import pytest

from src.core.metrics import ServiceMetricsCollector
from src.core.settings import Settings
from src.services import RedisService, WeaviateClient
from src.services.factory import ServiceFactory


@pytest.fixture
async def settings() -> Settings:
    """Create test settings."""
    return Settings(
        redis_url="redis://localhost:6379/0",
        redis_pool_size=10,
        weaviate_url="http://localhost:8080",
        weaviate_api_key="",
        weaviate_batch_size=100,
        redis_max_connections=50,
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


class TestServicePerformance:
    """Test service performance characteristics."""

    async def measure_operation_time(self, operation) -> float:
        """Measure operation execution time.

        Args:
            operation: Async operation to measure

        Returns:
            float: Operation duration in seconds
        """
        start_time = time.perf_counter()
        await operation
        return time.perf_counter() - start_time

    @pytest.mark.asyncio
    async def test_redis_operation_latency(self, redis_service: RedisService):
        """Test Redis operation latency under various conditions."""
        # Single operation latency
        key, value = "test_key", "test_value"
        set_time = await self.measure_operation_time(redis_service.set(key, value))
        get_time = await self.measure_operation_time(redis_service.get(key))

        # Assert performance SLOs
        assert set_time < 0.01, f"Set operation too slow: {set_time:.3f}s"
        assert get_time < 0.01, f"Get operation too slow: {get_time:.3f}s"

        # Batch operation latency
        batch_size = 1000
        keys = [f"batch_key_{i}" for i in range(batch_size)]
        values = [f"value_{i}" for i in range(batch_size)]

        # Measure batch set
        batch_set_time = await self.measure_operation_time(
            asyncio.gather(*[redis_service.set(k, v) for k, v in zip(keys, values, strict=False)])
        )

        # Measure batch get
        batch_get_time = await self.measure_operation_time(
            asyncio.gather(*[redis_service.get(k) for k in keys])
        )

        # Calculate throughput
        set_throughput = batch_size / batch_set_time
        get_throughput = batch_size / batch_get_time

        # Assert minimum throughput
        assert set_throughput > 1000, f"Set throughput too low: {set_throughput:.0f} ops/s"
        assert get_throughput > 1000, f"Get throughput too low: {get_throughput:.0f} ops/s"

    @pytest.mark.asyncio
    async def test_redis_concurrent_performance(self, redis_service: RedisService):
        """Test Redis performance under concurrent load."""
        num_clients = 50
        ops_per_client = 100

        async def client_workload(client_id: int) -> list[float]:
            """Simulate client workload."""
            latencies = []
            for i in range(ops_per_client):
                key = f"client_{client_id}_key_{i}"
                start_time = time.perf_counter()
                await redis_service.set(key, f"value_{i}")
                await redis_service.get(key)
                latencies.append(time.perf_counter() - start_time)
            return latencies

        # Run concurrent clients
        all_latencies = await asyncio.gather(*[client_workload(i) for i in range(num_clients)])

        # Analyze latencies
        flat_latencies = [lat for client_lats in all_latencies for lat in client_lats]
        avg_latency = mean(flat_latencies)
        p95_latency = np.percentile(flat_latencies, 95)
        p99_latency = np.percentile(flat_latencies, 99)

        # Assert performance characteristics
        assert avg_latency < 0.01, f"Average latency too high: {avg_latency:.3f}s"
        assert p95_latency < 0.05, f"P95 latency too high: {p95_latency:.3f}s"
        assert p99_latency < 0.1, f"P99 latency too high: {p99_latency:.3f}s"

    @pytest.mark.asyncio
    async def test_weaviate_vector_search_performance(self, weaviate_service: WeaviateClient):
        """Test Weaviate vector search performance."""
        # Create test vectors
        num_vectors = 1000
        vector_dim = 128
        test_vectors = [np.random.rand(vector_dim).tolist() for _ in range(num_vectors)]

        # Index vectors
        objects = [
            {"id": f"test_{i}", "vector": vec, "properties": {"value": f"test_value_{i}"}}
            for i, vec in enumerate(test_vectors)
        ]

        # Measure indexing time
        index_time = await self.measure_operation_time(weaviate_service.batch_add_objects(objects))

        # Assert indexing performance
        index_throughput = num_vectors / index_time
        assert (
            index_throughput > 100
        ), f"Indexing throughput too low: {index_throughput:.0f} vectors/s"

        # Test search latency
        query_vector = np.random.rand(vector_dim).tolist()
        search_times = []

        for _ in range(10):
            search_time = await self.measure_operation_time(
                weaviate_service.search_vectors(query_vector, limit=10)
            )
            search_times.append(search_time)

        avg_search_time = mean(search_times)
        assert avg_search_time < 0.1, f"Average search time too high: {avg_search_time:.3f}s"

    @pytest.mark.asyncio
    async def test_weaviate_batch_performance(self, weaviate_service: WeaviateClient):
        """Test Weaviate batch operation performance."""
        # Test different batch sizes
        batch_sizes = [10, 50, 100, 500]
        vector_dim = 128

        for batch_size in batch_sizes:
            # Create test batch
            objects = [
                {
                    "id": f"batch_test_{i}",
                    "vector": np.random.rand(vector_dim).tolist(),
                    "properties": {"value": f"batch_value_{i}"},
                }
                for i in range(batch_size)
            ]

            # Measure batch add time
            batch_time = await self.measure_operation_time(
                weaviate_service.batch_add_objects(objects)
            )

            # Calculate and assert throughput
            throughput = batch_size / batch_time
            min_throughput = 50  # Minimum objects per second
            assert throughput > min_throughput, (
                f"Batch throughput too low for size {batch_size}: " f"{throughput:.0f} objects/s"
            )

            # Verify objects are searchable
            query_vector = np.random.rand(vector_dim).tolist()
            results = await weaviate_service.search_vectors(query_vector, limit=1)
            assert len(results) > 0, "Search failed after batch insert"

    @pytest.mark.asyncio
    async def test_service_resource_usage(
        self, redis_service: RedisService, weaviate_service: WeaviateClient
    ):
        """Test service resource usage under load."""
        # Configure metrics collectors
        redis_metrics = ServiceMetricsCollector(
            service_name="redis",
            max_history=1000,
            memory_threshold_mb=500,
        )
        weaviate_metrics = ServiceMetricsCollector(
            service_name="weaviate",
            max_history=1000,
            memory_threshold_mb=500,
        )

        redis_service._metrics = redis_metrics
        weaviate_service._metrics = weaviate_metrics

        # Generate load
        async def generate_load():
            # Redis load
            for i in range(1000):
                await redis_service.set(f"load_key_{i}", f"load_value_{i}")

            # Weaviate load
            vectors = [
                {
                    "id": f"load_test_{i}",
                    "vector": np.random.rand(128).tolist(),
                    "properties": {"value": f"load_value_{i}"},
                }
                for i in range(100)
            ]
            await weaviate_service.batch_add_objects(vectors)

        # Run load test
        await generate_load()

        # Check metrics
        redis_resource_usage = redis_metrics.get_current_metrics()["resource_usage"]
        weaviate_resource_usage = weaviate_metrics.get_current_metrics()["resource_usage"]

        # Assert reasonable resource usage
        assert redis_resource_usage["memory_mb"] < 500, "Redis memory usage too high"
        assert weaviate_resource_usage["memory_mb"] < 1000, "Weaviate memory usage too high"
