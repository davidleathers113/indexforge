"""Tests for model caching.

This module contains tests for model caching functionality.
"""

import pytest
from sentence_transformers import SentenceTransformer

from src.services.ml.errors import ResourceError
from src.services.ml.monitoring.metrics import MetricsCollector
from src.services.ml.optimization.caching import ModelCache
from src.services.ml.optimization.resources import ResourceManager


@pytest.fixture
def metrics_collector(mocker):
    """Mock metrics collector."""
    collector = mocker.Mock(spec=MetricsCollector)
    collector.track_operation.return_value.__enter__ = mocker.Mock()
    collector.track_operation.return_value.__exit__ = mocker.Mock()
    return collector


@pytest.fixture
def resource_manager(mocker):
    """Mock resource manager."""
    manager = mocker.Mock(spec=ResourceManager)
    manager.check_memory.return_value = True
    return manager


@pytest.fixture
def model_cache(metrics_collector, resource_manager):
    """Create model cache instance."""
    return ModelCache[SentenceTransformer](
        metrics=metrics_collector,
        resources=resource_manager,
        max_entries=2,
        min_hit_count=2,
    )


class TestModelCache:
    """Tests for ModelCache."""

    async def test_get_uncached_model(self, model_cache):
        """Test getting uncached model."""
        model = await model_cache.get_model("test_model")
        assert model is None

    async def test_cache_and_get_model(self, model_cache, mocker):
        """Test caching and retrieving model."""
        mock_model = mocker.Mock(spec=SentenceTransformer)

        # Cache model
        await model_cache.cache_model("test_model", mock_model, memory_mb=100.0)

        # Access twice to meet min_hit_count
        await model_cache.cache_model("test_model", mock_model, memory_mb=100.0)

        # Get cached model
        cached_model = await model_cache.get_model("test_model")
        assert cached_model is mock_model

    async def test_eviction_on_capacity(self, model_cache, mocker):
        """Test model eviction when cache is full."""
        model1 = mocker.Mock(spec=SentenceTransformer)
        model2 = mocker.Mock(spec=SentenceTransformer)
        model3 = mocker.Mock(spec=SentenceTransformer)

        # Cache models up to capacity
        for model in [(model1, "model1"), (model2, "model2")]:
            # Access twice to meet min_hit_count
            for _ in range(2):
                await model_cache.cache_model(model[1], model[0], memory_mb=100.0)

        # Access model1 to increase its hit count
        await model_cache.get_model("model1")

        # Try to cache another model
        await model_cache.cache_model("model3", model3, memory_mb=100.0)
        await model_cache.cache_model("model3", model3, memory_mb=100.0)

        # Verify model2 was evicted (least used)
        assert await model_cache.get_model("model1") is model1
        assert await model_cache.get_model("model2") is None
        assert await model_cache.get_model("model3") is model3

    async def test_memory_constraint(self, model_cache, resource_manager, mocker):
        """Test caching with memory constraints."""
        model = mocker.Mock(spec=SentenceTransformer)
        resource_manager.check_memory.return_value = False

        with pytest.raises(ResourceError):
            await model_cache.cache_model("test_model", model, memory_mb=100.0)
            await model_cache.cache_model("test_model", model, memory_mb=100.0)

    async def test_hit_count_threshold(self, model_cache, mocker):
        """Test hit count threshold for caching."""
        model = mocker.Mock(spec=SentenceTransformer)

        # Single access shouldn't cache
        await model_cache.cache_model("test_model", model, memory_mb=100.0)
        assert await model_cache.get_model("test_model") is None

        # Second access should cache
        await model_cache.cache_model("test_model", model, memory_mb=100.0)
        assert await model_cache.get_model("test_model") is model

    async def test_metrics_tracking(self, model_cache, metrics_collector, mocker):
        """Test metrics are tracked for cache operations."""
        model = mocker.Mock(spec=SentenceTransformer)

        # Cache and access model
        await model_cache.cache_model("test_model", model, memory_mb=100.0)
        await model_cache.cache_model("test_model", model, memory_mb=100.0)
        await model_cache.get_model("test_model")

        # Verify metrics were tracked
        assert metrics_collector.track_operation.call_count >= 2
        metrics_collector.track_operation.assert_any_call(
            "cache_store", metadata={"model_id": "test_model", "memory_mb": 100.0}
        )
        metrics_collector.track_operation.assert_any_call(
            "cache_hit", metadata={"model_id": "test_model"}
        )
