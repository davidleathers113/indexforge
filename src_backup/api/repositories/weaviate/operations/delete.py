"""Weaviate deletion operations for v4.x."""

import logging

from weaviate.collections import Collection

from src.api.errors.weaviate_error_handling import with_weaviate_error_handling
from src.api.repositories.weaviate.base import BaseWeaviateRepository


logger = logging.getLogger(__name__)


class DeleteRepository(BaseWeaviateRepository):
    """Repository for deletion operations in Weaviate v4.x."""

    def __init__(self, collection: Collection):
        """Initialize with collection."""
        super().__init__(collection)

    @with_weaviate_error_handling
    async def batch_delete_documents(self, document_ids: list[str]) -> list[dict]:
        """Delete multiple documents using v4.x batch deletion.

        Args:
            document_ids: List of document IDs to delete

        Returns:
            List of results with status for each document
        """
        results = []

        try:
            # Use v4.x collection API for batch deletion
            deleted = await self.collection.batch.delete_objects(
                where={
                    "operator": "Or",
                    "operands": [
                        {"path": ["id"], "operator": "Equal", "valueString": doc_id}
                        for doc_id in document_ids
                    ],
                }
            )

            # Process results
            for doc_id in document_ids:
                if doc_id in deleted.successful:
                    results.append({"id": doc_id, "status": "success"})
                else:
                    error = next((err for err in deleted.failed if err.id == doc_id), None)
                    results.append(
                        {
                            "id": doc_id,
                            "status": "error",
                            "error": str(error.error) if error else "Unknown error",
                        }
                    )

            return results

        except Exception as e:
            logger.error(f"Batch deletion failed: {e!s}")
            # Add failure results for all documents
            results.extend(
                [{"id": doc_id, "status": "error", "error": str(e)} for doc_id in document_ids]
            )
            raise
