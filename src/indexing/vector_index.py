"""Facade for vector index operations.

This module provides a facade for vector index operations, offering a simplified
interface for document indexing while maintaining backward compatibility with
existing code.

Features:
1. Index Operations:
   - Document indexing
   - Document updates
   - Document deletion
   - Batch processing

2. Search Capabilities:
   - Semantic search
   - Hybrid search
   - Time-range search
   - Relationship search

3. Resource Management:
   - Connection handling
   - Cache management
   - Batch processing
   - Error handling

Usage:
    ```python
    from src.indexing.vector_index import VectorIndex

    # Create vector index
    index = VectorIndex(
        client_url="http://localhost:8080",
        class_name="Document",
        batch_size=100
    )

    # Perform operations
    index.add_documents(documents)
    results = index.semantic_search(query_vector, limit=10)
    ```

Note:
    - Implements facade pattern
    - Maintains compatibility
    - Provides caching support
    - Handles errors gracefully
"""

from datetime import datetime
import json
import logging
from typing import Any, Dict, List

import weaviate

from src.indexing.index.vector_index import VectorIndex as NewVectorIndex


class VectorIndex(NewVectorIndex):
    """Backward-compatible facade for vector index operations.

    This class provides a simplified interface for vector index operations
    while maintaining compatibility with existing code. It handles document
    indexing, searching, and caching operations.

    Attributes:
        client: Weaviate client instance
        class_name: Name of the document class
        batch_size: Size of batches for bulk operations
        operations: Handler for index operations
        logger: Logger instance for operation tracking
    """

    def __init__(self, client_url, class_name, batch_size, schema_validator=None, test_mode=False):
        """Initialize vector index with backward compatibility.

        Args:
            client_url: URL of the Weaviate instance
            class_name: Name of the document class
            batch_size: Size of batches for bulk operations
            schema_validator: Optional schema validator instance
            test_mode: Whether to run in test mode

        Example:
            >>> index = VectorIndex(
            ...     client_url="http://localhost:8080",
            ...     class_name="Document",
            ...     batch_size=100
            ... )
        """
        super().__init__(
            client_url=client_url,
            class_name=class_name,
            batch_size=batch_size,
            schema_validator=schema_validator,
            test_mode=test_mode,
        )
        self.logger = logging.getLogger(__name__)
        self._batch_size = batch_size  # Store batch size locally

    @property
    def class_name(self) -> str:
        """Get the class name.

        Returns:
            Name of the document class in Weaviate
        """
        return self.operations.class_name

    @property
    def batch_size(self) -> int:
        """Get the batch size.

        Returns:
            Size of batches for bulk operations
        """
        return self._batch_size

    @batch_size.setter
    def batch_size(self, value: int) -> None:
        """Set the batch size.

        Args:
            value: New batch size for bulk operations
        """
        self._batch_size = value
        if hasattr(self, "operations"):
            self.operations.documents.batch_size = value

    def initialize(self) -> None:
        """Initialize the vector index.

        Performs necessary setup and validation for the index.
        """
        super().initialize()

    def time_range_search(
        self, start_time: datetime, end_time: datetime, query_vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search documents within a time range.

        Args:
            start_time: Start of the time range
            end_time: End of the time range
            query_vector: Query embedding vector
            limit: Maximum number of results (default: 10)

        Returns:
            List of matching documents with scores
        """
        return self.operations.search.time_range_search(start_time, end_time, query_vector, limit)

    def relationship_search(
        self, parent_id: str, query_vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search documents by relationship.

        Args:
            parent_id: ID of the parent document
            query_vector: Query embedding vector
            limit: Maximum number of results (default: 10)

        Returns:
            List of related documents with scores
        """
        return self.operations.search.relationship_search(parent_id, query_vector, limit)

    def get_all_documents(self) -> List[str]:
        """Retrieve all document IDs from the index.

        Returns:
            List of document IDs in the index
        """
        try:
            result = self.client.data_object.get(class_name=self.class_name)
            document_ids = [doc["id"] for doc in result["objects"]]
            return document_ids
        except Exception as e:
            self.logger.error(f"Error retrieving documents: {str(e)}")
            return []

    def update_document(self, document_id, updates):
        """Update a document in the index.

        Args:
            document_id: ID of the document to update
            updates: Dictionary of updates to apply

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Updating document {document_id}")
        self.logger.debug(f"Updates: {updates}, vector update: no")
        try:
            return self.operations.update_document(document_id, updates)
        except Exception as e:
            self.logger.error(f"Error updating document {document_id}: {str(e)}")
            return False

    def add_documents(self, documents, deduplicate=False):
        """Add documents to the index.

        Args:
            documents: List of documents to add
            deduplicate: Whether to check for duplicates (default: False)

        Returns:
            List of added document IDs
        """
        if deduplicate:
            # Generate a cache key based on document content
            cache_key = self._generate_cache_key(documents)
            cached_doc_ids = self.cache_manager.get(cache_key)
            if cached_doc_ids:
                self.logger.debug(f"Documents found in cache with key: {cache_key}")
                return cached_doc_ids
            else:
                self.logger.debug(f"No cache entry found for key: {cache_key}")
        # Proceed to add documents
        doc_ids = self.operations.add_documents(documents)
        if deduplicate:
            # Store the doc_ids in cache
            self.cache_manager.set(cache_key, doc_ids)
        return doc_ids

    def _generate_cache_key(self, documents):
        """Generate a cache key based on document content.

        Args:
            documents: List of documents to generate key for

        Returns:
            Cache key string
        """
        # Create a stable representation of documents for hashing
        doc_str = json.dumps(documents, sort_keys=True)
        return f"docs:{hash(doc_str)}"

    def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents from the index.

        Args:
            document_ids: List of document IDs to delete

        Returns:
            True if all documents were deleted successfully
        """
        self.logger.info(f"Deleting documents: {document_ids}")
        try:
            return self.operations.delete_documents(doc_ids=document_ids)
        except Exception as e:
            self.logger.error(f"Error deleting documents: {str(e)}")
            return False

    def cleanup(self):
        """Clean up resources.

        Ensures proper cleanup of all resources used by the index.
        """
        try:
            # Call base class cleanup
            super().cleanup()

            # Clean up any additional resources specific to the facade
            self.logger.info("VectorIndex facade resources cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            raise

    def semantic_search(
        self, query_vector: List[float], limit: int = 10, min_score: float = 0.0
    ) -> List[Dict]:
        """Search documents by semantic similarity.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results (default: 10)
            min_score: Minimum similarity score (default: 0.0)

        Returns:
            List of search results with scores
        """
        try:
            return self.operations.search.semantic_search(
                query_vector=query_vector,
                limit=limit,
                min_score=min_score,
            )
        except Exception as e:
            self.logger.error(f"Error in semantic search: {str(e)}")
            return []

    def hybrid_search(
        self,
        text_query: str,
        query_vector: List[float],
        limit: int = 10,
        alpha: float = 0.5,
    ) -> List[Dict]:
        """Search documents using hybrid approach.

        Args:
            text_query: Text to search for
            query_vector: Query embedding vector
            limit: Maximum number of results (default: 10)
            alpha: Weight between text and vector search (default: 0.5)

        Returns:
            List of search results with scores
        """
        try:
            return self.operations.search.hybrid_search(text_query, query_vector, limit, alpha)
        except Exception as e:
            self.logger.error(f"Error in hybrid search: {str(e)}")
            return []


# Explicitly re-export weaviate for test mocking
__all__ = ["VectorIndex", "weaviate"]
