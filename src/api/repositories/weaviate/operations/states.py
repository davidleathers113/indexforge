"""Batch operation states."""

import logging
from typing import Dict, List

from src.api.repositories.weaviate.operations.base import BatchOperation, BatchOperationState

logger = logging.getLogger(__name__)


class InitialState(BatchOperationState):
    """Initial state for batch operations."""

    def process(self, operation: BatchOperation, items: List[Dict]) -> List[Dict]:
        """Process items in initial state."""
        operation.performance_tracker.start_batch(len(items))
        return items


class ProcessingState(BatchOperationState):
    """Processing state for batch operations."""

    def process(self, operation: BatchOperation, items: List[Dict]) -> List[Dict]:
        """Process items in batch."""
        results = []
        successful = 0
        failed = 0

        try:
            with operation.collection.batch as batch:
                batch.configure(batch_size=len(items), dynamic=True, timeout_retries=3)

                for item in items:
                    try:
                        batch.add_object(**item)
                        successful += 1
                    except Exception as e:
                        logger.error(f"Failed to add item: {str(e)}")
                        results.append(
                            {"id": item.get("id", "unknown"), "status": "error", "error": str(e)}
                        )
                        failed += 1

            operation.metrics.record_batch_completion()
            return results

        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            operation.metrics.record_batch_error()
            raise


class CompletionState(BatchOperationState):
    """Completion state for batch operations."""

    def process(self, operation: BatchOperation, items: List[Dict]) -> List[Dict]:
        """Process completion of batch operation."""
        successful = sum(1 for item in items if item.get("status") != "error")
        failed = len(items) - successful

        operation.performance_tracker.end_batch(
            successful_objects=successful, failed_objects=failed
        )
        return items


class ErrorState(BatchOperationState):
    """Error state for batch operations."""

    def process(self, operation: BatchOperation, items: List[Dict]) -> List[Dict]:
        """Process error state."""
        operation.performance_tracker.end_batch(successful_objects=0, failed_objects=len(items))
        operation.metrics.record_batch_error()
        return [
            {"id": item.get("id", "unknown"), "status": "error", "error": "Batch operation failed"}
            for item in items
        ]
