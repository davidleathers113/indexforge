"""Base classes for batch operations."""

from abc import ABC, abstractmethod
import logging
from typing import Protocol

from weaviate.collections import Collection

from src.api.repositories.weaviate.metrics import BatchMetrics, BatchPerformanceTracker


logger = logging.getLogger(__name__)


class BatchOperationState(Protocol):
    """Protocol for batch operation states."""

    def process(self, operation: "BatchOperation", items: list[dict]) -> list[dict]:
        """Process batch items in current state."""
        ...


class BatchOperation(ABC):
    """Template for batch operations."""

    def __init__(self, collection: Collection, batch_size: int | None = None):
        """Initialize batch operation."""
        self.collection = collection
        self.batch_size = batch_size or 100
        self.metrics = BatchMetrics()
        self.performance_tracker = BatchPerformanceTracker(
            min_batch_size=50, max_batch_size=500, window_size=10
        )

    @abstractmethod
    def prepare_item(self, item: dict) -> dict:
        """Prepare an item for batch operation."""
        pass

    @abstractmethod
    def validate_item(self, item: dict) -> bool:
        """Validate an item before processing."""
        pass

    @abstractmethod
    def process_batch(self, batch: list[dict]) -> list[dict]:
        """Process a batch of items."""
        pass

    def execute_batch(self, items: list[dict]) -> list[dict]:
        """Execute batch operation using template method."""
        results = []
        current_batch = []
        batch_size = self.batch_size

        try:
            for item in items:
                if not self.validate_item(item):
                    results.append(self._create_error_result(item, "Validation failed"))
                    continue

                prepared_item = self.prepare_item(item)
                current_batch.append(prepared_item)

                if len(current_batch) >= batch_size:
                    batch_results = self.process_batch(current_batch)
                    results.extend(batch_results)
                    current_batch = []

            if current_batch:
                batch_results = self.process_batch(current_batch)
                results.extend(batch_results)

            return results

        except Exception as e:
            logger.error(f"Batch operation failed: {e!s}")
            for item in current_batch:
                results.append(self._create_error_result(item, str(e)))
            raise

    def _create_error_result(self, item: dict, error: str) -> dict:
        """Create error result for failed operation."""
        return {"id": item.get("id", "unknown"), "status": "error", "error": error}