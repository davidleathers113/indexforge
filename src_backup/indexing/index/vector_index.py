"""
High-level interface for interacting with the vector database.

This module provides the VectorIndex class which serves as the main entry point
for all vector database operations. It abstracts away the complexity of direct
database interactions and provides a simple, intuitive interface for document
management and search operations.

The interface handles:
- Document management (add, update, delete)
- Vector similarity search
- Hybrid text and vector search
- Schema management
- Resource cleanup
- Comprehensive logging

Example:
    ```python
    # Create a vector index instance
    index = VectorIndex(
        client_url="http://localhost:8080",
        class_name="Document",
        batch_size=100
    )

    # Initialize the index
    index.initialize()

    # Add documents
    docs = [
        {
            "content": "First document",
            "metadata": {"source": "file1"}
        },
        {
            "content": "Second document",
            "metadata": {"source": "file2"}
        }
    ]
    doc_ids = index.add_documents(docs)

    # Perform search
    results = index.semantic_search(
        query_vector=[0.1, 0.2, 0.3],
        limit=5,
        min_score=0.8
    )

    # Clean up when done
    index.cleanup()
    ```
"""

import logging

from src.indexing.search import SearchResult

from .index_config import IndexConfig, IndexInitializer
from .index_operations import IndexOperations


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class VectorIndex:
    """
    High-level interface for vector database operations.

    This class provides a simplified interface for interacting with the vector
    database, handling all aspects of document management and search operations.
    It coordinates between various components to provide a seamless experience
    for working with vector embeddings and document search.

    Features:
    - Simple document management (add, update, delete)
    - Semantic search using vector similarity
    - Hybrid search combining text and vectors
    - Automatic schema management
    - Resource cleanup handling
    - Comprehensive logging

    Attributes:
        operations: IndexOperations instance for core functionality
        _initialized: Whether the index has been initialized

    Example:
        ```python
        # Create and initialize index
        index = VectorIndex(client_url="http://localhost:8080")
        index.initialize()

        # Add a document
        doc_id = index.add_documents([{
            "content": "Example document",
            "metadata": {"source": "test"}
        }])[0]

        # Update the document
        index.update_document(
            doc_id,
            {"content": "Updated content"},
            vector=[0.1, 0.2, 0.3]
        )

        # Search for similar documents
        results = index.semantic_search(
            query_vector=[0.1, 0.2, 0.3],
            limit=5
        )

        # Clean up
        index.cleanup()
        ```
    """

    def __init__(
        self,
        client_url: str = "http://localhost:8080",
        class_name: str = "Document",
        batch_size: int = 100,
        test_mode: bool = False,
        schema_validator=None,
    ):
        """
        Initialize a new VectorIndex instance.

        Creates a new vector index instance with the specified configuration.
        Sets up all necessary components including client connection, cache
        management, and operations interface.

        Args:
            client_url: URL of the Weaviate instance (default: "http://localhost:8080")
            class_name: Name of the document class (default: "Document")
            batch_size: Number of documents to process in each batch (default: 100)
            test_mode: Whether to run in test mode (default: False)
            schema_validator: Optional custom schema validator

        Raises:
            ConnectionError: If unable to connect to Weaviate
            ValueError: If configuration parameters are invalid

        Example:
            ```python
            # Default configuration for local development
            index = VectorIndex()

            # Custom configuration for production
            prod_index = VectorIndex(
                client_url="http://weaviate.prod:8080",
                class_name="ProductionDocs",
                batch_size=500
            )
            ```
        """
        logger.info(f"Initializing VectorIndex with class_name={class_name}, test_mode={test_mode}")
        config = IndexConfig(
            client_url=client_url,
            class_name=class_name,
            batch_size=batch_size,
        )
        initializer = IndexInitializer(config)
        client, cache_manager = initializer.initialize()
        logger.debug("Initialized client and cache manager")

        self.operations = IndexOperations(
            client,
            class_name,
            batch_size,
            cache_manager,
            test_mode=test_mode,
            schema_validator=schema_validator,
        )
        logger.debug("Created IndexOperations instance")
        self._initialized = False

    def initialize(self) -> None:
        """
        Initialize the vector index schema and prepare it for use.

        This method ensures the database schema is properly set up and
        ready for operations. It should be called before performing any
        document operations.

        Raises:
            Exception: If initialization fails

        Example:
            ```python
            index = VectorIndex()
            try:
                index.initialize()
                print("Index is ready for use")
            except Exception as e:
                print(f"Failed to initialize index: {e}")
            ```
        """
        logger.info("Initializing vector index")
        self.operations.initialize()
        self._initialized = True

    @property
    def is_initialized(self) -> bool:
        """
        Check if the index has been initialized.

        Returns:
            bool: True if the index has been initialized, False otherwise

        Example:
            ```python
            index = VectorIndex()
            if not index.is_initialized:
                index.initialize()
            ```
        """
        return self._initialized

    def get_schema(self) -> dict | None:
        """
        Get the current schema configuration.

        Returns:
            Optional[Dict]: The current schema configuration if initialized,
                          None otherwise

        Example:
            ```python
            schema = index.get_schema()
            if schema:
                print(f"Schema version: {schema.get('version')}")
            else:
                print("Index not initialized")
            ```
        """
        if not self.is_initialized:
            return None
        return self.operations.schema.validator.get_schema()

    def add_documents(self, documents: list[dict], deduplicate: bool = True) -> list[str]:
        """
        Add multiple documents to the vector index.

        This method adds documents to the index, optionally performing
        deduplication. It automatically handles initialization if needed
        and processes documents in batches for efficiency.

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
                doc_ids = index.add_documents(docs)
                print(f"Added {len(doc_ids)} documents")
            except ValueError as e:
                print(f"Invalid document format: {e}")
            ```
        """
        logger.info(f"Adding {len(documents)} documents (deduplicate={deduplicate})")
        doc_ids = self.operations.add_documents(documents, deduplicate)
        logger.debug(f"Added documents with IDs: {doc_ids}")
        return doc_ids

    def delete_documents(self, doc_ids: list[str]) -> bool:
        """
        Delete multiple documents from the index.

        This method removes the specified documents from the index. It operates
        in batch mode for efficiency and includes proper error handling.

        Args:
            doc_ids: List of document IDs to delete

        Returns:
            bool: True if all deletions were successful, False otherwise

        Example:
            ```python
            ids_to_delete = ["doc1", "doc2", "doc3"]
            if index.delete_documents(ids_to_delete):
                print("Successfully deleted all documents")
            else:
                print("Some deletions may have failed")
            ```
        """
        logger.info(f"Deleting documents: {doc_ids}")
        success = self.operations.delete_documents(doc_ids)
        logger.debug(f"Delete operation {'succeeded' if success else 'failed'}")
        return success

    def update_document(
        self, doc_id: str, updates: dict, vector: list[float] | None = None
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

            if index.update_document("doc123", updates, new_vector):
                print("Document updated successfully")
            else:
                print("Update failed")
            ```
        """
        logger.info(f"Updating document {doc_id}")
        logger.debug(f"Updates: {updates}, vector update: {'yes' if vector else 'no'}")
        success = self.operations.update_document(doc_id, updates, vector)
        logger.debug(f"Update operation {'succeeded' if success else 'failed'}")
        return success

    def semantic_search(
        self,
        query_vector: list[float],
        limit: int = 10,
        min_score: float = 0.7,
        additional_props: list[str] | None = None,
    ) -> list[SearchResult]:
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
            results = index.semantic_search(
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
        return self.operations.semantic_search(query_vector, limit, min_score, additional_props)

    def hybrid_search(
        self,
        text_query: str,
        query_vector: list[float],
        limit: int = 10,
        alpha: float = 0.5,
        additional_props: list[str] | None = None,
    ) -> list[SearchResult]:
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
            results = index.hybrid_search(
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
        return self.operations.hybrid_search(
            text_query, query_vector, limit, alpha, additional_props
        )

    def cleanup(self):
        """
        Clean up resources used by the vector index.

        This method ensures proper cleanup of all resources including:
        - Cache manager connections
        - Database client connections
        - Any other managed resources

        It should be called when the index is no longer needed to prevent
        resource leaks.

        Raises:
            Exception: If cleanup operations fail

        Example:
            ```python
            index = VectorIndex()
            try:
                # Use the index...
                results = index.semantic_search(...)
            finally:
                index.cleanup()  # Ensure resources are cleaned up
            ```
        """
        try:
            # Clean up cache manager
            if hasattr(self.operations, "cache_manager"):
                self.operations.cache_manager.cleanup()

            # Clean up Weaviate client
            if hasattr(self.operations, "client"):
                self.operations.client.close()

            logger.info("VectorIndex resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e!s}")
            raise
