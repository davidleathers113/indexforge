"""Batch operations for Weaviate."""

import logging

import weaviate.classes as wvc

from .base import BaseWeaviateRepository
from .metrics import BatchMetrics, BatchPerformanceTracker
from .operations.deletion import DeleteOperation
from .operations.indexing import IndexOperation


logger = logging.getLogger(__name__)


class BatchRepository(BaseWeaviateRepository):
    """Repository for batch operations in Weaviate."""

    def __init__(
        self,
        client: wvc.WeaviateClient,
        collection: str,
        min_batch_size: int = 50,
        max_batch_size: int = 500,
    ):
        """Initialize batch repository.

        Args:
            client: Weaviate client instance
            collection: Collection name to operate on
            min_batch_size: Minimum batch size for operations
            max_batch_size: Maximum batch size for operations
        """
        super().__init__(client, collection)
        self.metrics = BatchMetrics()
        self.performance_tracker = BatchPerformanceTracker(
            min_batch_size=min_batch_size, max_batch_size=max_batch_size, window_size=10
        )

    def index_documents(self, documents: list[dict]) -> dict:
        """Index a batch of documents."""
        if not documents:
            return {"status": "success", "message": "No documents to process"}

        operation = IndexOperation(
            self.collection_ref, batch_size=self.performance_tracker.get_optimal_batch_size()
        )

        try:
            results = operation.execute_batch(documents)
            return {
                "status": "success",
                "processed": len(results),
                "metrics": self.metrics.get_summary(),
            }
        except Exception as e:
            logger.error(f"Failed to index documents: {e!s}")
            return {"status": "error", "message": str(e), "metrics": self.metrics.get_summary()}

    def delete_documents(self, document_ids: list[dict]) -> dict:
        """Delete a batch of documents."""
        if not document_ids:
            return {"status": "success", "message": "No documents to delete"}

        operation = DeleteOperation(
            self.collection_ref, batch_size=self.performance_tracker.get_optimal_batch_size()
        )

        try:
            results = operation.execute_batch(document_ids)
            return {
                "status": "success",
                "processed": len(results),
                "metrics": self.metrics.get_summary(),
            }
        except Exception as e:
            logger.error(f"Failed to delete documents: {e!s}")
            return {"status": "error", "message": str(e), "metrics": self.metrics.get_summary()}
