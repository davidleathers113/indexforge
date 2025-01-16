"""Performance tests for service operations."""

import asyncio
import time
from statistics import mean, stdev
from typing import Any, Dict, List

import numpy as np
import pytest

from src.core.settings import Settings
from src.services import RedisService, WeaviateClient
from src.services.factory import ServiceFactory

from .analysis import analyze_performance_trend, save_analysis
from .conftest import PerformanceThresholds
from .utils import PerformanceMetrics, measure_async_operation


@pytest.fixture
async def settings() -> Settings:
    """Create test settings with performance-oriented configurations."""
    return Settings(
        redis_url="redis://localhost:6379/0",
        redis_pool_size=50,  # Larger pool for performance testing
        weaviate_url="http://localhost:8080",
        weaviate_api_key="",
        batch_size=1000,
        operation_timeout=30,
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
    """Performance tests for service operations."""

    async def measure_operation_time(self, operation, iterations: int = 100) -> Dict[str, float]:
        """Measure operation time statistics."""
        times: List[float] = []
        for _ in range(iterations):
            start = time.perf_counter()
            await operation()
            end = time.perf_counter()
            times.append(end - start)

        return {
            "avg": mean(times),
            "min": min(times),
            "max": max(times),
            "stdev": stdev(times) if len(times) > 1 else 0,
            "p95": sorted(times)[int(0.95 * len(times))],
        }

    @pytest.mark.asyncio
    async def test_redis_operation_latency(
        self,
        redis_service: RedisService,
        performance_metrics_path,
        performance_thresholds: PerformanceThresholds,
        performance_baseline: Dict[str, Any],
    ):
        """Test Redis operation latency against thresholds and baseline."""
        metrics = PerformanceMetrics("redis_operations", performance_metrics_path)

        # Test single operations
        for i in range(100):
            key = f"test_key_{i}"
            value = f"test_value_{i}"

            await measure_async_operation(redis_service.set, metrics, key=key, value=value)

            await measure_async_operation(redis_service.get, metrics, key=key)

        stats = metrics.get_statistics()
        metrics.save_metrics()

        # Assert against thresholds
        assert stats["duration_ms"]["p95"] < performance_thresholds.max_operation_time_ms
        # Assert against baseline with 10% tolerance
        baseline_p95 = performance_baseline["redis"]["single_op_p95_ms"]
        assert stats["duration_ms"]["p95"] < baseline_p95 * 1.1

    @pytest.mark.asyncio
    async def test_redis_concurrent_performance(
        self,
        redis_service: RedisService,
        performance_metrics_path,
        performance_thresholds: PerformanceThresholds,
    ):
        """Test Redis performance under concurrent load."""
        metrics = PerformanceMetrics("redis_concurrent", performance_metrics_path)

        async def concurrent_operation(i: int):
            key = f"concurrent_key_{i}"
            value = f"concurrent_value_{i}"
            await measure_async_operation(redis_service.set, metrics, key=key, value=value)

        # Run concurrent operations
        tasks = [concurrent_operation(i) for i in range(50)]
        await asyncio.gather(*tasks)

        stats = metrics.get_statistics()
        metrics.save_metrics()

        assert stats["duration_ms"]["p95"] < performance_thresholds.max_operation_time_ms
        assert len(stats["duration_ms"]) == 50  # Verify all operations completed

    @pytest.mark.asyncio
    async def test_weaviate_vector_search_performance(
        self,
        weaviate_service: WeaviateClient,
        performance_metrics_path,
        performance_thresholds: PerformanceThresholds,
        performance_baseline: Dict[str, Any],
    ):
        """Test Weaviate vector search performance."""
        metrics = PerformanceMetrics("weaviate_vector_search", performance_metrics_path)

        # Create test vectors
        test_vectors = [[float(i) for i in range(10)] for _ in range(100)]

        # Test vector search operations
        for vector in test_vectors[:10]:  # Use subset for search tests
            await measure_async_operation(
                weaviate_service.vector_search, metrics, vector=vector, limit=5
            )

        stats = metrics.get_statistics()
        metrics.save_metrics()

        # Assert against thresholds
        assert stats["duration_ms"]["p95"] < performance_thresholds.max_operation_time_ms
        # Assert against baseline with 10% tolerance
        baseline_p95 = performance_baseline["weaviate"]["vector_search_p95_ms"]
        assert stats["duration_ms"]["p95"] < baseline_p95 * 1.1

    @pytest.mark.asyncio
    async def test_weaviate_batch_performance(
        self,
        weaviate_service: WeaviateClient,
        performance_metrics_path,
        performance_thresholds: PerformanceThresholds,
    ):
        """Test Weaviate batch operation performance."""
        metrics = PerformanceMetrics("weaviate_batch", performance_metrics_path)

        # Create test batch
        batch_size = 100
        test_objects = [
            {
                "id": f"test_{i}",
                "vector": [float(j) for j in range(10)],
                "properties": {"value": f"test_value_{i}"},
            }
            for i in range(batch_size)
        ]

        # Test batch operation
        await measure_async_operation(
            weaviate_service.batch_create_objects, metrics, objects=test_objects
        )

        stats = metrics.get_statistics()
        metrics.save_metrics()

        assert stats["duration_ms"]["p95"] < performance_thresholds.max_batch_operation_time_ms
        assert stats["memory_mb"]["max"] < performance_thresholds.max_memory_usage_mb

    @pytest.mark.asyncio
    async def test_sustained_performance(
        self,
        redis_service: RedisService,
        weaviate_service: WeaviateClient,
        performance_metrics_path,
        performance_thresholds: PerformanceThresholds,
    ):
        """Test performance over an extended period."""
        redis_metrics = PerformanceMetrics("redis_sustained", performance_metrics_path)
        weaviate_metrics = PerformanceMetrics("weaviate_sustained", performance_metrics_path)

        # Test duration and operation interval
        duration_seconds = 300  # 5 minutes
        operation_interval = 0.1  # 100ms between operations

        start_time = time.time()
        operation_count = 0

        while time.time() - start_time < duration_seconds:
            # Redis operations
            key = f"sustained_{operation_count}"
            value = f"test_value_{operation_count}"
            await measure_async_operation(redis_service.set, redis_metrics, key=key, value=value)

            # Weaviate operations
            if operation_count % 10 == 0:  # Less frequent vector operations
                vector = [float(i) for i in range(10)]
                await measure_async_operation(
                    weaviate_service.vector_search, weaviate_metrics, vector=vector, limit=5
                )

            operation_count += 1
            await asyncio.sleep(operation_interval)

        # Analyze Redis performance
        redis_stats = redis_metrics.get_statistics()
        redis_metrics.save_metrics()

        redis_analysis = analyze_performance_trend(performance_metrics_path, "redis_sustained")
        save_analysis(redis_analysis, performance_metrics_path)

        # Analyze Weaviate performance
        weaviate_stats = weaviate_metrics.get_statistics()
        weaviate_metrics.save_metrics()

        weaviate_analysis = analyze_performance_trend(
            performance_metrics_path, "weaviate_sustained"
        )
        save_analysis(weaviate_analysis, performance_metrics_path)

        # Assertions
        assert redis_stats["duration_ms"]["p95"] < performance_thresholds.max_operation_time_ms
        assert redis_stats["memory_mb"]["max"] < performance_thresholds.max_memory_usage_mb
        assert redis_stats["cpu_percent"]["p95"] < 80  # CPU usage should stay reasonable

        assert weaviate_stats["duration_ms"]["p95"] < performance_thresholds.max_operation_time_ms
        assert weaviate_stats["memory_mb"]["max"] < performance_thresholds.max_memory_usage_mb
        assert weaviate_stats["cpu_percent"]["p95"] < 80

        # Check for performance degradation
        assert not redis_analysis.get("regressions"), "Redis performance should not degrade"
        assert not weaviate_analysis.get("regressions"), "Weaviate performance should not degrade"
