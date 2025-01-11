"""Weaviate batch operations for v4.x."""

import asyncio
import logging
from typing import Dict, List, Optional

import psutil
from weaviate.collections import Collection
from weaviate.util import generate_uuid5

from src.api.errors.weaviate_error_handling import with_weaviate_error_handling
from src.api.repositories.weaviate.base import BaseWeaviateRepository
from src.api.repositories.weaviate.metrics import BatchMetrics, BatchPerformanceTracker

logger = logging.getLogger(__name__)


class BatchRepository(BaseWeaviateRepository):
    """Repository for batch operations in Weaviate v4.x."""

    def __init__(self, collection: Collection, batch_size: Optional[int] = None):
        """Initialize with collection and optional batch size."""
        super().__init__(collection)
        self.batch_size = batch_size or 100
        self.metrics = BatchMetrics()
        self.performance_tracker = BatchPerformanceTracker(
            min_batch_size=50, max_batch_size=500, window_size=10
        )

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    @with_weaviate_error_handling
    async def batch_index_documents(
        self, documents: List[Dict], batch_size: Optional[int] = None
    ) -> List[Dict]:
        """Index multiple documents in batches.

        Args:
            documents: List of documents to index
            batch_size: Optional override for batch size

        Returns:
            List of results with status for each document
        """
        results = []
        current_batch = []
        batch_size = batch_size or self.performance_tracker.get_optimal_batch_size()

        try:
            with self.collection.batch as batch:
                batch.configure(
                    batch_size=batch_size,
                    dynamic=True,
                    timeout_retries=3,
                    callback=self._on_batch_error,
                )

                for document in documents:
                    # Generate deterministic UUID based on file path
                    doc_id = generate_uuid5(document["file_path"])

                    # Add to current batch
                    current_batch.append({"id": doc_id, "document": document})

                    # Support named vectors if provided
                    vectors = document.pop("vectors", None)

                    # Add to batch with v4.x syntax
                    batch.add_object(
                        properties=document,
                        uuid=doc_id,
                        vectors=vectors,  # New in v4.x: named vectors support
                    )

                    # Process batch if size limit reached
                    if len(current_batch) >= batch_size:
                        self.performance_tracker.start_batch(len(current_batch))
                        await self._process_batch_results(current_batch, results)
                        self.performance_tracker.end_batch(
                            successful_objects=sum(
                                1
                                for r in results[-len(current_batch) :]
                                if r["status"] == "success"
                            ),
                            failed_objects=sum(
                                1 for r in results[-len(current_batch) :] if r["status"] == "error"
                            ),
                            memory_usage_mb=self._get_memory_usage(),
                        )
                        current_batch = []
                        self.metrics.record_batch_completion()

                # Process remaining documents
                if current_batch:
                    self.performance_tracker.start_batch(len(current_batch))
                    await self._process_batch_results(current_batch, results)
                    self.performance_tracker.end_batch(
                        successful_objects=sum(
                            1 for r in results[-len(current_batch) :] if r["status"] == "success"
                        ),
                        failed_objects=sum(
                            1 for r in results[-len(current_batch) :] if r["status"] == "error"
                        ),
                        memory_usage_mb=self._get_memory_usage(),
                    )
                    self.metrics.record_batch_completion()

            return results

        except Exception as e:
            logger.error(f"Batch indexing failed: {str(e)}")
            # Add failure results for remaining documents
            for item in current_batch:
                results.append(
                    {
                        "id": item["id"],
                        "file_path": item["document"]["file_path"],
                        "status": "error",
                        "error": str(e),
                    }
                )
            self.metrics.record_batch_error()
            if self.current_batch_start is not None:
                self.performance_tracker.end_batch(
                    successful_objects=0,
                    failed_objects=len(current_batch),
                    memory_usage_mb=self._get_memory_usage(),
                )
            raise

    def _on_batch_error(self, batch_results: List[Dict]) -> None:
        """Handle batch operation errors with v4.x error format."""
        for result in batch_results:
            if "errors" in result:
                self.logger.error(f"Batch error: {result['errors']}")
                self.metrics.record_object_error()

    async def _process_batch_results(self, batch_items: List[Dict], results: List[Dict]) -> None:
        """Process results for a batch of documents with v4.x validation."""
        await asyncio.sleep(0)  # Allow batch processing

        for item in batch_items:
            try:
                # Verify document using v4.x collection API
                doc = await self._get_document_by_id(item["id"])
                if doc:
                    results.append(
                        {
                            "id": item["id"],
                            "file_path": item["document"]["file_path"],
                            "status": "success",
                        }
                    )
                    self.metrics.record_object_success()
                else:
                    results.append(
                        {
                            "id": item["id"],
                            "file_path": item["document"]["file_path"],
                            "status": "error",
                            "error": "Document not found after indexing",
                        }
                    )
                    self.metrics.record_object_error()
            except Exception as e:
                results.append(
                    {
                        "id": item["id"],
                        "file_path": item["document"]["file_path"],
                        "status": "error",
                        "error": str(e),
                    }
                )
                self.metrics.record_object_error()

    async def _get_document_by_id(self, document_id: str) -> Optional[Dict]:
        """Get document by ID using v4.x collection API."""
        try:
            # Use v4.x collection API
            result = (
                self.collection.query.fetch_objects()
                .with_where({"path": ["id"], "operator": "Equal", "valueString": document_id})
                .with_limit(1)
                .do()
            )
            return result.objects[0] if result.objects else None
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {str(e)}")
            return None
