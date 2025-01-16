"""Performance test suite for critical system components.

This module provides comprehensive performance testing with:
- Detailed timing metrics
- Memory usage tracking
- Resource utilization monitoring
- Batch processing benchmarks
"""

import asyncio
import gc
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import psutil
import pytest

from src.core.settings import Settings
from src.ml.processing.models.chunks import Chunk, ChunkBatch
from src.ml.processing.validation.validators.batch import BatchValidator
from src.ml.processing.validation.validators.language import LanguageValidator
from src.services import RedisService, WeaviateClient
from src.services.factory import ServiceFactory


class PerformanceMetrics:
    """Collects and analyzes performance metrics."""

    def __init__(self) -> None:
        """Initialize metrics collection."""
        self.operation_times: List[float] = []
        self.memory_usage: List[float] = []
        self.batch_sizes: List[int] = []
        self.error_counts: Dict[str, int] = {}
        self.start_time: Optional[float] = None

    def start_operation(self) -> None:
        """Start timing an operation."""
        gc.collect()  # Force garbage collection for accurate memory measurement
        self.start_time = time.perf_counter()
        self.memory_usage.append(psutil.Process().memory_info().rss / 1024 / 1024)  # MB

    def end_operation(self) -> float:
        """End timing an operation and record metrics.

        Returns:
            float: Operation duration in seconds
        """
        if self.start_time is None:
            raise ValueError("Operation not started")

        duration = time.perf_counter() - self.start_time
        self.operation_times.append(duration)
        self.start_time = None
        return duration

    def get_statistics(self) -> Dict[str, float]:
        """Calculate performance statistics.

        Returns:
            Dict[str, float]: Performance metrics
        """
        if not self.operation_times:
            return {}

        return {
            "avg_time": np.mean(self.operation_times),
            "median_time": np.median(self.operation_times),
            "p95_time": np.percentile(self.operation_times, 95),
            "max_time": max(self.operation_times),
            "min_time": min(self.operation_times),
            "avg_memory_mb": np.mean(self.memory_usage),
            "max_memory_mb": max(self.memory_usage),
        }


@pytest.fixture
async def performance_metrics() -> PerformanceMetrics:
    """Create performance metrics collector."""
    return PerformanceMetrics()


@pytest.fixture
async def settings() -> Settings:
    """Create test settings."""
    return Settings(
        redis_url="redis://localhost:6379/0",
        redis_pool_size=10,
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


class TestValidationPerformance:
    """Performance tests for validation components."""

    @pytest.mark.asyncio
    async def test_language_validation_performance(
        self,
        redis_service: RedisService,
        performance_metrics: PerformanceMetrics,
    ):
        """Test language validation performance with caching."""
        # Setup
        validator = LanguageValidator(
            supported_languages={"en", "es", "fr"},
            cache_service=redis_service,
            min_content_length=50,
        )

        # Generate test data
        test_chunks = [
            Chunk(
                content=f"This is test content number {i} with sufficient length to trigger validation."
                * 5
            )
            for i in range(100)
        ]

        # Test uncached performance
        for chunk in test_chunks[:10]:
            performance_metrics.start_operation()
            await validator.validate(chunk)
            duration = performance_metrics.end_operation()
            assert duration < 0.1, "Language validation should complete within 100ms"

        # Test cached performance
        for chunk in test_chunks[:10]:  # Same chunks to hit cache
            performance_metrics.start_operation()
            await validator.validate(chunk)
            duration = performance_metrics.end_operation()
            assert duration < 0.01, "Cached validation should complete within 10ms"

        stats = performance_metrics.get_statistics()
        assert stats["p95_time"] < 0.1, "95th percentile should be under 100ms"
        assert stats["max_memory_mb"] < 500, "Memory usage should stay under 500MB"

    @pytest.mark.asyncio
    async def test_batch_validation_performance(
        self,
        performance_metrics: PerformanceMetrics,
    ):
        """Test batch validation performance with different sizes."""
        validator = BatchValidator(
            max_batch_size=1000,
            max_memory_mb=500,
            chunk_processing_timeout=30.0,
        )

        # Test different batch sizes
        for batch_size in [10, 100, 500, 1000]:
            chunks = [
                Chunk(
                    content=f"Batch test content {i}",
                    metadata={"key": f"value{i}", "batch": str(i // 100)},
                )
                for i in range(batch_size)
            ]
            batch = ChunkBatch(chunks=chunks)

            performance_metrics.start_operation()
            errors = validator.validate(chunks[0], {"batch": batch})
            duration = performance_metrics.end_operation()
            performance_metrics.batch_sizes.append(batch_size)

            # Assertions
            assert not errors, f"Validation for batch size {batch_size} should not produce errors"
            assert (
                duration < 0.1
            ), f"Batch validation for size {batch_size} should complete within 100ms"
            memory_usage = performance_metrics.memory_usage[-1]
            assert (
                memory_usage < 500
            ), f"Memory usage for batch size {batch_size} should stay under 500MB"

        # Analyze scaling behavior
        stats = performance_metrics.get_statistics()
        correlation = np.corrcoef(
            performance_metrics.batch_sizes, performance_metrics.operation_times
        )[0, 1]
        assert correlation < 0.8, "Performance should not degrade linearly with batch size"
        assert stats["max_memory_mb"] < 500, "Peak memory usage should stay under limit"


class TestServicePerformance:
    """Performance tests for service operations."""

    @pytest.mark.asyncio
    async def test_redis_pipeline_performance(
        self,
        redis_service: RedisService,
        performance_metrics: PerformanceMetrics,
    ):
        """Test Redis pipeline performance with different batch sizes."""
        # Test different pipeline sizes
        for size in [10, 100, 500, 1000]:
            operations = [("set", f"key{i}", [f"value{i}"]) for i in range(size)]

            performance_metrics.start_operation()
            results = await redis_service.pipeline_execute(operations)
            duration = performance_metrics.end_operation()

            assert all(results), f"All operations in batch size {size} should succeed"
            assert duration < 0.5, f"Pipeline of size {size} should complete within 500ms"

        stats = performance_metrics.get_statistics()
        assert stats["p95_time"] < 0.5, "95th percentile should be under 500ms"

    @pytest.mark.asyncio
    async def test_weaviate_batch_performance(
        self,
        weaviate_service: WeaviateClient,
        performance_metrics: PerformanceMetrics,
    ):
        """Test Weaviate batch operation performance."""
        class_name = "TestClass"

        # Test different batch sizes
        for size in [10, 50, 100]:
            # Generate test data
            test_objects = [
                {
                    "text": f"test document {i}",
                    "category": chr(65 + (i % 26)),
                    "timestamp": datetime.now().isoformat(),
                }
                for i in range(size)
            ]
            vectors = [np.random.rand(128).tolist() for _ in range(size)]

            performance_metrics.start_operation()
            uuids = await weaviate_service.batch_add_objects(
                class_name=class_name,
                objects=test_objects,
                vectors=vectors,
                batch_size=size,
            )
            duration = performance_metrics.end_operation()

            assert len(uuids) == size, f"All objects in batch size {size} should be created"
            assert (
                duration < 2.0
            ), f"Batch operation of size {size} should complete within 2 seconds"

            # Cleanup
            await weaviate_service.delete_batch(class_name, uuids)

        stats = performance_metrics.get_statistics()
        assert stats["p95_time"] < 2.0, "95th percentile should be under 2 seconds"
        assert stats["max_memory_mb"] < 500, "Memory usage should stay under 500MB"
