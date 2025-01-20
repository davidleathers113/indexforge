"""Performance benchmarks for ML services.

This module provides comprehensive performance benchmarks focusing on:
1. Operation latency measurements
2. Memory usage patterns
3. Batch processing efficiency
4. Resource utilization metrics
"""

import asyncio
import time
from typing import List, Optional
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from src.core.settings import Settings
from src.services.ml.implementations.embedding import EmbeddingService
from src.services.ml.implementations.factories import ServiceFactory
from src.services.ml.monitoring.instrumentation import (
    InstrumentationConfig,
    PerformanceInstrumentor,
)
from src.services.ml.monitoring.metrics import MetricsCollector
from src.services.ml.optimization.resources import ResourceManager


class BenchmarkData(BaseModel):
    """Benchmark data model."""

    text: str
    size_bytes: int
    expected_latency_ms: Optional[float] = None


@pytest.fixture
def settings():
    """Create settings for benchmarks."""
    return Settings(
        max_memory_mb=2000,
        batch_size=10,
        min_batch_size=2,
        max_batch_size=100,
        device="cpu",
        model_path="test_model",
    )


@pytest.fixture
def metrics_collector():
    """Create metrics collector."""
    return MetricsCollector()


@pytest.fixture
def resource_manager(settings):
    """Create resource manager."""
    return ResourceManager(settings)


@pytest.fixture
def instrumentor(metrics_collector, resource_manager):
    """Create performance instrumentor."""
    config = InstrumentationConfig(
        collect_profiles=True,
        track_resources=True,
        alert_thresholds={
            "duration_ms": 1000.0,
            "memory_mb": 1000.0,
            "cpu_percent": 80.0,
        },
    )
    return PerformanceInstrumentor(metrics_collector, resource_manager, config)


@pytest.fixture
async def service(settings, instrumentor):
    """Create service for benchmarking."""
    service = await ServiceFactory.create_embedding_service(settings)
    service.set_instrumentor(instrumentor)
    return service


class TestPerformanceBenchmarks:
    """Performance benchmark test suite."""

    @pytest.mark.benchmark
    async def test_operation_latency(self, service: EmbeddingService):
        """Benchmark operation latency under different loads."""
        # Test data with increasing sizes
        test_data = [
            BenchmarkData(
                text="test" * (1000 * i),
                size_bytes=4000 * i,
                expected_latency_ms=50.0 * i,
            )
            for i in range(1, 6)
        ]

        latencies = []
        for data in test_data:
            start_time = time.perf_counter()
            await service.embed_text(data.text)
            latency = (time.perf_counter() - start_time) * 1000

            latencies.append(latency)

            # Verify latency is within expected range
            assert latency <= data.expected_latency_ms * 1.5, (
                f"Latency {latency:.2f}ms exceeded threshold " f"for size {data.size_bytes} bytes"
            )

        # Verify latency correlation with input size
        assert all(l2 >= l1 for l1, l2 in zip(latencies, latencies[1:]))

    @pytest.mark.benchmark
    async def test_memory_usage_patterns(self, service: EmbeddingService):
        """Benchmark memory usage patterns."""
        # Create test data with varying memory requirements
        test_sizes = [1000, 5000, 10000, 50000]
        test_data = [BenchmarkData(text="test" * size, size_bytes=size * 4) for size in test_sizes]

        for data in test_data:
            # Process text and collect memory metrics
            await service.embed_text(data.text)

            # Get memory metrics
            metrics = service._instrumentor._metrics.get_metrics("embed_text")
            latest_metric = metrics[-1]

            # Verify memory usage scales with input size
            memory_ratio = latest_metric.memory_mb * 1024 * 1024 / data.size_bytes
            assert 1.0 <= memory_ratio <= 10.0, (
                f"Unexpected memory usage ratio {memory_ratio:.2f} "
                f"for size {data.size_bytes} bytes"
            )

    @pytest.mark.benchmark
    async def test_batch_processing_efficiency(self, service: EmbeddingService, settings: Settings):
        """Benchmark batch processing efficiency."""
        batch_sizes = [5, 10, 20, 50]
        efficiency_metrics = []

        for size in batch_sizes:
            # Create batch
            batch = [BenchmarkData(text="test" * 100, size_bytes=400) for _ in range(size)]

            # Process batch and measure throughput
            start_time = time.perf_counter()
            results = await service.embed_batch([data.text for data in batch])
            duration = time.perf_counter() - start_time

            # Calculate items per second
            throughput = size / duration
            efficiency_metrics.append(throughput)

            # Verify throughput improves with batch size
            if len(efficiency_metrics) > 1:
                improvement = throughput / efficiency_metrics[-2]
                assert improvement >= 0.8, (
                    f"Batch size {size} showed unexpected efficiency drop: "
                    f"{improvement:.2f}x previous throughput"
                )

    @pytest.mark.benchmark
    async def test_resource_utilization(self, service: EmbeddingService):
        """Benchmark resource utilization metrics."""
        # Test scenarios with different resource requirements
        scenarios = [
            ("single", 1, 1000),  # Single large text
            ("batch", 10, 100),  # Medium batch of smaller texts
            ("concurrent", 5, 500),  # Concurrent medium texts
        ]

        for scenario, count, size in scenarios:
            # Create test data
            if scenario == "single":
                data = BenchmarkData(text="test" * size, size_bytes=size * 4)
                await service.embed_text(data.text)
            elif scenario == "batch":
                batch = [
                    BenchmarkData(text="test" * size, size_bytes=size * 4) for _ in range(count)
                ]
                await service.embed_batch([data.text for data in batch])
            else:  # concurrent
                tasks = [service.embed_text("test" * size) for _ in range(count)]
                await asyncio.gather(*tasks)

            # Get resource metrics
            metrics = service._instrumentor._metrics.get_resource_metrics(f"embed_{scenario}")
            latest_metric = metrics[-1]

            # Verify resource utilization
            assert 0 <= latest_metric.cpu_percent <= 100
            assert latest_metric.memory_mb > 0
            if hasattr(latest_metric, "gpu_memory_mb"):
                assert latest_metric.gpu_memory_mb is None or latest_metric.gpu_memory_mb > 0

    @pytest.mark.benchmark
    async def test_concurrent_performance(self, service: EmbeddingService):
        """Benchmark performance under concurrent load."""
        concurrency_levels = [2, 4, 8]

        for level in concurrency_levels:
            # Create concurrent operations
            data = BenchmarkData(text="test" * 1000, size_bytes=4000)
            tasks = [service.embed_text(data.text) for _ in range(level)]

            # Measure execution time
            start_time = time.perf_counter()
            await asyncio.gather(*tasks)
            duration = time.perf_counter() - start_time

            # Calculate throughput
            throughput = level / duration

            # Verify reasonable scaling
            assert throughput >= level * 0.5, (
                f"Poor scaling at concurrency level {level}: " f"{throughput:.2f} operations/second"
            )

    @pytest.mark.benchmark
    async def test_memory_stability(self, service: EmbeddingService):
        """Benchmark memory stability during extended operation."""
        # Run repeated operations and monitor memory
        iterations = 10
        memory_measurements = []

        for _ in range(iterations):
            # Process medium-sized batch
            batch = [BenchmarkData(text="test" * 1000, size_bytes=4000) for _ in range(10)]
            await service.embed_batch([data.text for data in batch])

            # Record memory usage
            metrics = service._instrumentor._metrics.get_metrics("embed_batch")
            memory_measurements.append(metrics[-1].memory_mb)

        # Verify memory stability
        max_variation = max(memory_measurements) - min(memory_measurements)
        assert max_variation <= 100.0, (
            f"Unstable memory usage detected: {max_variation:.2f}MB variation "
            f"over {iterations} iterations"
        )
