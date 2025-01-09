"""
Provides core operations for managing and querying the vector index.

This module contains the IndexOperations class which serves as the main interface
for all vector index operations including document management, search operations,
and schema maintenance. It integrates various components to provide a complete
solution for vector search functionality.

Key features:
- Document addition, deletion, and updates
- Semantic and hybrid search capabilities
- Schema management and validation
- Optional caching support
- Batch processing for bulk operations
- Comprehensive error handling and logging

Example:
    ```python
    import weaviate
    from src.utils.cache_manager import CacheManager

    # Initialize components
    client = weaviate.Client("http://localhost:8080")
    cache = CacheManager(host="localhost", port=6379)

    # Create operations instance
    ops = IndexOperations(
        client=client,
        class_name="Document",
        batch_size=100,
        cache_manager=cache
    )

    # Add documents
    docs = [
        {"content": "First document", "metadata": {...}},
        {"content": "Second document", "metadata": {...}}
    ]
    doc_ids = ops.add_documents(docs)

    # Perform search
    results = ops.semantic_search(
        query_vector=[0.1, 0.2, 0.3],
        limit=5,
        min_score=0.8
    )
    ```
"""

import logging
from typing import Dict, List, Optional

import weaviate

from src.indexing.document import DocumentStorage
from src.indexing.schema import SchemaMigrator
from src.indexing.search import SearchExecutor, SearchResult
from src.utils.cache_manager import CacheManager


class IndexOperations:
    """
    Main interface for vector index operations and management.

    This class provides a comprehensive interface for interacting with the
    vector index, including document operations, search functionality, and
    schema management. It coordinates between various components to provide
    a complete vector search solution.

    Features:
    - Document management (add, update, delete)
    - Vector search operations (semantic and hybrid)
    - Schema validation and migration
    - Optional result caching
    - Batch processing for efficiency
    - Comprehensive logging

    Attributes:
        client: Weaviate client instance for database operations
        class_name: Name of the document class in Weaviate
        batch_size: Size of batches for bulk operations
        schema: Schema migrator for managing database schema
        documents: Document storage manager
        search: Search executor for query operations
        logger: Logger instance for operation tracking

    Example:
        ```python
        ops = IndexOperations(
            client=weaviate.Client("http://localhost:8080"),
            class_name="Document",
            batch_size=100
        )

        # Initialize the index
        ops.initialize()

        # Add some documents
        doc_ids = ops.add_documents([
            {
                "content": "Example document",
                "metadata": {"source": "test"}
            }
        ])

        # Search for similar documents
        results = ops.semantic_search(
            query_vector=[0.1, 0.2, 0.3],
            limit=5
        )
        ```
    """

    def __init__(
        self,
        client: weaviate.Client,
        class_name: str,
        batch_size: int,
        cache_manager: Optional[CacheManager] = None,
        test_mode: bool = False,
        schema_validator=None,
    ):
        """
        Initialize a new IndexOperations instance.

        Creates a new operations instance with the specified configuration.
        Sets up all necessary components for index operations including
        schema management, document storage, and search capabilities.

        Args:
            client: Configured Weaviate client instance
            class_name: Name of the document class to manage
            batch_size: Number of documents to process in each batch
            cache_manager: Optional cache manager for result caching
            test_mode: Whether to run in test mode (default: False)
            schema_validator: Optional custom schema validator

        Raises:
            TypeError: If client is not a weaviate.Client instance
            ValueError: If class_name is empty or batch_size < 1
        """
        self.client = client
        self.class_name = class_name
        self.batch_size = batch_size

        self.schema = SchemaMigrator(client, class_name, schema_validator=schema_validator)
        self.documents = DocumentStorage(
            client, class_name, batch_size, cache_manager, test_mode=test_mode
        )
        self.search = SearchExecutor(client, class_name)
        self.logger = logging.getLogger(__name__)

    def initialize(self) -> None:
        """
        Initialize the index schema and ensure it's ready for use.

        This method ensures that the database schema is properly set up
        and migrated to the latest version if necessary. It should be
        called before performing any operations that require the schema.

        Raises:
            Exception: If schema initialization fails

        Example:
            ```python
            ops = IndexOperations(client, "Document", 100)
            try:
                ops.initialize()
                print("Index is ready for use")
            except Exception as e:
                print(f"Failed to initialize index: {e}")
            ```
        """
        try:
            self.schema.ensure_schema()
        except Exception as e:
            msg = f"Error initializing index: {str(e)}"
            self.logger.error(msg)
            raise

    def add_documents(self, documents: List[Dict], deduplicate: bool = True) -> List[str]:
        """
        Add a batch of documents to the index.

        This method adds multiple documents to the index, optionally performing
        deduplication. It handles initialization of the schema if needed and
        processes documents in batches for efficiency.

        Args:
            documents: List of document dictionaries to add. Each document
                     should contain 'content' and 'metadata' fields.
            deduplicate: Whether to check for and skip duplicate documents
                        (default: True)

        Returns:
            List[str]: List of IDs for the added documents

        Raises:
            ValueError: If documents are malformed
            Exception: If document addition fails

        Example:
            ```python
            docs = [
                {
                    "content": "First document",
                    "metadata": {"source": "file1", "date": "2023-01-01"}
                },
                {
                    "content": "Second document",
                    "metadata": {"source": "file2", "date": "2023-01-02"}
                }
            ]

            try:
                doc_ids = ops.add_documents(docs)
                print(f"Added {len(doc_ids)} documents")
            except ValueError as e:
                print(f"Invalid document format: {e}")
            ```
        """
        try:
            self.initialize()  # Ensure schema exists
            return self.documents.add_documents(documents, deduplicate)
        except Exception as e:
            msg = f"Error adding documents: {str(e)}"
            self.logger.error(msg)
            raise

    def delete_documents(self, doc_ids: List[str]) -> bool:
        """
        Delete multiple documents from the index by their IDs.

        This method removes the specified documents from the index. It operates
        in batch mode for efficiency and includes proper error handling.

        Args:
            doc_ids: List of document IDs to delete

        Returns:
            bool: True if all deletions were successful, False otherwise

        Example:
            ```python
            ids_to_delete = ["doc1", "doc2", "doc3"]
            if ops.delete_documents(ids_to_delete):
                print("Successfully deleted all documents")
            else:
                print("Some deletions may have failed")
            ```
        """
        return self.documents.delete_documents(doc_ids)

    def update_document(
        self, doc_id: str, updates: Dict, vector: Optional[List[float]] = None
    ) -> bool:
        """
        Update a document's properties and optionally its vector.

        This method updates specific properties of a document and optionally
        its vector embedding. It handles partial updates, meaning only
        specified fields will be modified.

        Args:
            doc_id: ID of the document to update
            updates: Dictionary of properties to update
            vector: Optional new vector embedding for the document

        Returns:
            bool: True if update was successful, False otherwise

        Example:
            ```python
            updates = {
                "content": "Updated content",
                "metadata": {"last_modified": "2023-01-01"}
            }
            new_vector = [0.1, 0.2, 0.3]  # Optional

            if ops.update_document("doc123", updates, new_vector):
                print("Document updated successfully")
            else:
                print("Update failed")
            ```
        """
        return self.documents.update_document(doc_id, updates, vector)

    def semantic_search(
        self,
        query_vector: List[float],
        limit: int = 10,
        min_score: float = 0.7,
        additional_props: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Perform semantic search using vector similarity.

        This method searches for documents similar to the provided query vector
        using cosine similarity. It returns results ordered by similarity score.

        Args:
            query_vector: Vector embedding to search with
            limit: Maximum number of results to return (default: 10)
            min_score: Minimum similarity score threshold (default: 0.7)
            additional_props: Additional properties to include in results

        Returns:
            List[SearchResult]: List of search results ordered by similarity

        Example:
            ```python
            # Search with a query vector
            results = ops.semantic_search(
                query_vector=[0.1, 0.2, 0.3],
                limit=5,
                min_score=0.8,
                additional_props=["category", "author"]
            )

            # Process results
            for result in results:
                print(f"Score: {result.score}")
                print(f"Content: {result.content}")
            ```
        """
        return self.search.semantic_search(query_vector, limit, min_score, additional_props)

    def hybrid_search(
        self,
        text_query: str,
        query_vector: List[float],
        limit: int = 10,
        alpha: float = 0.5,
        additional_props: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining text and vector similarity.

        This method combines traditional text search with vector similarity
        search. The alpha parameter controls the balance between text and
        vector similarity in the final results.

        Args:
            text_query: Text string to search for
            query_vector: Vector embedding for similarity search
            limit: Maximum number of results to return (default: 10)
            alpha: Weight between text (0) and vector (1) search (default: 0.5)
            additional_props: Additional properties to include in results

        Returns:
            List[SearchResult]: List of search results ordered by combined score

        Example:
            ```python
            # Perform hybrid search
            results = ops.hybrid_search(
                text_query="machine learning",
                query_vector=[0.1, 0.2, 0.3],
                limit=5,
                alpha=0.7
            )

            # Process results
            for result in results:
                print(f"Score: {result.score}")
                print(f"Title: {result.content.get('title')}")
            ```
        """
        return self.search.hybrid_search(text_query, query_vector, limit, alpha, additional_props)
