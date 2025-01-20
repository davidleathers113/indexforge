"""Model caching for ML services.

This module provides caching capabilities for ML models with resource-aware
eviction strategies and performance monitoring.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, TypeVar

from src.services.ml.errors import ResourceError
from src.services.ml.monitoring.metrics import MetricsCollector
from src.services.ml.optimization.resources import ResourceManager

logger = logging.getLogger(__name__)

T = TypeVar("T")  # Model type


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry for model instances."""

    model: T
    last_accessed: float
    memory_mb: float
    hit_count: int = 0


class ModelCache(Generic[T]):
    """Resource-aware model cache manager."""

    def __init__(
        self,
        metrics: MetricsCollector,
        resources: ResourceManager,
        max_entries: int = 5,
        min_hit_count: int = 10,
    ) -> None:
        """Initialize cache manager.

        Args:
            metrics: Metrics collector for tracking
            resources: Resource manager for constraints
            max_entries: Maximum number of cached models
            min_hit_count: Minimum hits before caching
        """
        self._metrics = metrics
        self._resources = resources
        self._max_entries = max_entries
        self._min_hit_count = min_hit_count
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._access_counts: Dict[str, int] = {}

    async def get_model(self, model_id: str) -> Optional[T]:
        """Get model from cache.

        Args:
            model_id: Model identifier

        Returns:
            Cached model if available
        """
        entry = self._cache.get(model_id)
        if entry:
            with self._metrics.track_operation("cache_hit", metadata={"model_id": model_id}):
                entry.last_accessed = time.time()
                entry.hit_count += 1
                return entry.model
        return None

    async def cache_model(self, model_id: str, model: T, memory_mb: float) -> None:
        """Cache model if beneficial.

        Args:
            model_id: Model identifier
            model: Model instance to cache
            memory_mb: Model memory usage in MB

        Raises:
            ResourceError: If caching would exceed resource limits
        """
        # Track access for caching decisions
        self._access_counts[model_id] = self._access_counts.get(model_id, 0) + 1

        # Only cache frequently used models
        if self._access_counts[model_id] < self._min_hit_count:
            logger.debug(
                f"Model {model_id} not cached (hits: {self._access_counts[model_id]} < "
                f"{self._min_hit_count})"
            )
            return

        with self._metrics.track_operation(
            "cache_store", metadata={"model_id": model_id, "memory_mb": memory_mb}
        ):
            # Check if we need to evict
            while len(self._cache) >= self._max_entries or not self._resources.check_memory(
                memory_mb
            ):
                if not self._evict_least_used():
                    raise ResourceError("Cannot cache model: insufficient memory after eviction")

            # Cache the model
            self._cache[model_id] = CacheEntry(
                model=model,
                last_accessed=time.time(),
                memory_mb=memory_mb,
            )
            logger.info(f"Cached model {model_id} ({memory_mb:.1f}MB)")

    def _evict_least_used(self) -> bool:
        """Evict least recently used model.

        Returns:
            True if eviction succeeded
        """
        if not self._cache:
            return False

        # Find least recently used
        lru_id = min(
            self._cache.items(),
            key=lambda x: (x[1].hit_count, x[1].last_accessed),
        )[0]

        # Evict and track
        evicted = self._cache.pop(lru_id)
        with self._metrics.track_operation(
            "cache_evict",
            metadata={
                "model_id": lru_id,
                "hits": evicted.hit_count,
                "memory_mb": evicted.memory_mb,
            },
        ):
            logger.info(
                f"Evicted model {lru_id} (hits: {evicted.hit_count}, "
                f"memory: {evicted.memory_mb:.1f}MB)"
            )
            return True
