"""Document batch operations module.

This module provides functionality for managing batched document operations in Weaviate,
including batch creation, document addition, error handling, and cleanup. It optimizes
document insertion by grouping multiple documents into batches for better performance.
"""

import logging

import weaviate


class BatchManager:
    """Manages batched document operations in Weaviate.

    This class handles the batching of document operations for efficient processing,
    including batch creation, document addition, error handling, and cleanup. It
    maintains a configurable batch size and provides detailed logging for debugging.

    Attributes:
        client (weaviate.Client): Weaviate client instance.
        class_name (str): Name of the document class in Weaviate.
        batch_size (int): Maximum number of documents per batch.
        test_mode (bool): Whether running in test mode.
        _current_batch: Current batch context manager.
        logger (logging.Logger): Logger instance for this class.
    """

    def __init__(
        self,
        client: weaviate.Client,
        class_name: str,
        batch_size: int,
        test_mode: bool = False,
    ):
        """Initialize the batch manager with specified configuration.

        Sets up the batch manager with the given Weaviate client and configuration,
        initializing logging and batch settings.

        Args:
            client: Weaviate client instance for database operations.
            class_name: Name of the document class in Weaviate.
            batch_size: Maximum number of documents per batch operation.
            test_mode: Whether to run in test mode (disables error callbacks).

        Example:
            ```python
            client = weaviate.Client("http://localhost:8080")
            batch_mgr = BatchManager(
                client=client,
                class_name="Document",
                batch_size=100,
                test_mode=False
            )
            ```
        """
        self.client = client
        self.class_name = class_name
        self.batch_size = batch_size
        self.test_mode = test_mode
        self._current_batch = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def add_document(self, properties: dict, vector: list[float], doc_id: str) -> None:
        """Add a document to the current batch for processing.

        Adds a document with its properties and vector to the current batch. If no
        batch exists, creates a new one. Handles batch configuration and provides
        detailed logging for debugging.

        Args:
            properties: Document properties dictionary to store.
            vector: Document embedding vector for vector search.
            doc_id: UUID string for the document.

        Raises:
            ValueError: If the document ID is not a valid UUID.
            Exception: For any other errors during document addition.

        Example:
            ```python
            properties = {
                "content": {"body": "Document text"},
                "metadata": {"title": "Doc Title"}
            }
            vector = [0.1, 0.2, 0.3]
            doc_id = "123e4567-e89b-12d3-a456-426614174000"
            batch_mgr.add_document(properties, vector, doc_id)
            ```
        """
        try:
            self.logger.debug(f"Attempting to add document with ID: {doc_id}")
            self.logger.debug(f"Document properties: {properties}")
            self.logger.debug(f"Vector length: {len(vector) if vector else 'None'}")

            if self._current_batch is None:
                self.logger.debug("Creating new batch")
                self._current_batch = self.client.batch.configure(
                    batch_size=self.batch_size,
                    callback=self._on_batch_error if not self.test_mode else None,
                )
                self._current_batch.__enter__()

            self._current_batch.add_data_object(
                data_object=properties,
                class_name=self.class_name,
                uuid=doc_id,
                vector=vector,
            )
            self.logger.debug(f"Successfully added document {doc_id} to batch")
        except ValueError as ve:
            self.logger.error(f"UUID validation error for document {doc_id}: {ve!s}")
            self.logger.error(f"UUID type: {type(doc_id)}, value: {doc_id}")
            raise
        except Exception as e:
            self.logger.error(f"Error adding document {doc_id}: {e!s}", exc_info=True)
            self.logger.error(f"Document properties that caused error: {properties}")
            raise

    def _on_batch_error(self, batch_results: list[dict]) -> None:
        """Handle errors that occur during batch operations.

        Processes batch operation results and logs any errors that occurred
        during the batch processing.

        Args:
            batch_results: List of results from the batch operation, each containing:
                - result: Operation result including any errors
                - object: The object that caused the error

        Note:
            This method is called automatically by Weaviate's batch processor
            when an error occurs during batch processing.
        """
        for result in batch_results:
            if "result" in result and "errors" in result["result"]:
                self.logger.error(f"Batch operation error: {result['result']['errors']}")
                self.logger.error(f"Failed object: {result.get('object', 'Unknown object')}")

    def __del__(self):
        """Clean up batch context and resources.

        Ensures proper cleanup of the batch context when the BatchManager
        instance is destroyed. Handles any errors during cleanup and logs
        them appropriately.

        Note:
            This method is called automatically when the BatchManager
            instance is garbage collected.
        """
        try:
            if self._current_batch is not None:
                self.logger.debug("Cleaning up batch context")
                self._current_batch.__exit__(None, None, None)
        except Exception as e:
            self.logger.error(f"Error cleaning up batch context: {e!s}", exc_info=True)
