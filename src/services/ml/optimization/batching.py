"""Dynamic batch sizing for ML services.

This module provides dynamic batch size optimization based on
resource utilization and performance metrics.
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, TypeVar

from src.core.models.chunks import Chunk
from src.services.ml.monitoring.metrics import MetricsCollector
from src.services.ml.optimization.resources import ResourceManager
from src.services.ml.validation.parameters import BatchValidationParameters

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class BatchMetrics:
    """Metrics for batch processing."""

    original_size: int
    actual_size: int
    memory_usage_mb: float
    duration_ms: float
    success: bool


class DynamicBatchSizer:
    """Manages dynamic batch sizing based on resource constraints."""

    def __init__(
        self,
        metrics: MetricsCollector,
        resources: ResourceManager,
        params: BatchValidationParameters,
    ) -> None:
        """Initialize batch sizer.

        Args:
            metrics: Metrics collector for tracking
            resources: Resource manager for constraints
            params: Batch validation parameters
        """
        self._metrics = metrics
        self._resources = resources
        self._params = params
        self._min_batch_size = 1
        self._current_size = params.max_batch_size

    async def process_batch(
        self, items: List[T], processor: Callable[[List[T]], List[Any]]
    ) -> List[Any]:
        """Process items with dynamic batch sizing.

        Args:
            items: Items to process
            processor: Batch processing function

        Returns:
            Processing results
        """
        if not items:
            return []

        batch_size = self._calculate_batch_size(items)
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            with self._metrics.track_operation(
                "batch_processing",
                batch_size=len(batch),
                metadata={"original_size": len(items)},
            ):
                batch_results = await self._resources.execute_with_resources(
                    lambda: processor(batch),
                    required_mb=self._estimate_batch_memory(batch),
                )
                results.extend(batch_results)

                # Update metrics and adjust batch size
                self._update_batch_size(len(batch))

        return results

    def _calculate_batch_size(self, items: List[T]) -> int:
        """Calculate optimal batch size.

        Args:
            items: Items to process

        Returns:
            Optimal batch size
        """
        # Start with current size
        size = min(self._current_size, len(items))

        # Check resource constraints
        memory_per_item = self._estimate_item_memory(items[0])
        max_items = int(self._resources.limits.max_memory_mb / memory_per_item)
        size = min(size, max_items)

        # Check performance metrics
        recent_metrics = self._metrics.get_metrics("batch_processing")
        if recent_metrics:
            # If recent batches are taking too long, reduce size
            avg_duration = sum(m.duration_ms for m in recent_metrics) / len(recent_metrics)
            if avg_duration > 5000:  # 5 seconds threshold
                size = max(self._min_batch_size, size // 2)

        return max(self._min_batch_size, min(size, self._params.max_batch_size))

    def _estimate_batch_memory(self, items: List[T]) -> float:
        """Estimate memory requirement for batch.

        Args:
            items: Items to process

        Returns:
            Estimated memory requirement in MB
        """
        if isinstance(items[0], Chunk):
            total_text_length = sum(len(chunk.text) for chunk in items)
            # Text memory (UTF-8 + processing overhead)
            text_memory = (total_text_length * 2) / 1024 / 1024
            # Base memory per chunk
            base_memory = len(items) * 0.5
            return text_memory + base_memory
        else:
            # Generic estimation for non-chunk items
            return len(items) * 1.0  # 1MB per item as baseline

    def _estimate_item_memory(self, item: T) -> float:
        """Estimate memory requirement for single item.

        Args:
            item: Item to process

        Returns:
            Estimated memory requirement in MB
        """
        if isinstance(item, Chunk):
            # Text memory + overhead
            return (len(item.text) * 2 / 1024 / 1024) + 0.5
        else:
            # Generic estimation
            return 1.0

    def _update_batch_size(self, last_batch_size: int) -> None:
        """Update batch size based on processing metrics.

        Args:
            last_batch_size: Size of last processed batch
        """
        recent_metrics = self._metrics.get_metrics("batch_processing")
        if not recent_metrics:
            return

        # Calculate success rate
        success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)

        # Adjust batch size based on success rate
        if success_rate > 0.95 and self._current_size < self._params.max_batch_size:
            # Gradually increase if very successful
            self._current_size = min(
                self._params.max_batch_size,
                int(self._current_size * 1.2),
            )
        elif success_rate < 0.8:
            # Quickly decrease if failing often
            self._current_size = max(
                self._min_batch_size,
                int(self._current_size * 0.5),
            )

        logger.debug(
            f"Updated batch size to {self._current_size} " f"(success rate: {success_rate:.2f})"
        )
