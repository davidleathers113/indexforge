"""Document addition operations module.

This module provides functionality for adding documents to the storage system,
including batch processing, deduplication, caching, and validation. It handles
the complete lifecycle of document addition from validation to storage.
"""

import logging
import uuid

import weaviate

from src.indexing.document.batch_manager import BatchManager
from src.indexing.document.document_processor import DocumentProcessor
from src.utils.cache_manager import CacheManager


class DocumentAddition:
    """Handles document addition operations in the storage system.

    This class manages the addition of documents to the storage system,
    including validation, processing, batching, and caching. It supports
    deduplication and provides detailed logging of the addition process.

    Attributes:
        client (weaviate.Client): Weaviate client instance for database operations.
        class_name (str): Name of the document class in Weaviate.
        batch_size (int): Maximum number of documents per batch.
        batch_manager (BatchManager): Manager for batch operations.
        processor (DocumentProcessor): Processor for document validation and preparation.
        cache_manager (Optional[CacheManager]): Manager for document caching.
        test_mode (bool): Whether running in test mode.
        logger (logging.Logger): Logger instance for this class.
    """

    def __init__(
        self,
        client: weaviate.Client,
        class_name: str,
        batch_size: int,
        batch_manager: BatchManager,
        processor: DocumentProcessor,
        cache_manager: CacheManager | None = None,
        test_mode: bool = False,
    ):
        """Initialize the document addition handler.

        Sets up the document addition handler with the specified configuration
        and initializes all necessary components.

        Args:
            client: Weaviate client instance for database operations.
            class_name: Name of the document class in Weaviate.
            batch_size: Maximum number of documents per batch.
            batch_manager: Manager for handling document batches.
            processor: Processor for document validation and preparation.
            cache_manager: Optional cache manager for document caching.
            test_mode: Whether to run in test mode (default: False).

        Example:
            ```python
            client = weaviate.Client("http://localhost:8080")
            adder = DocumentAddition(
                client=client,
                class_name="Document",
                batch_size=100,
                batch_manager=batch_mgr,
                processor=doc_processor,
                cache_manager=cache_mgr
            )
            ```
        """
        self.client = client
        self.class_name = class_name
        self.batch_size = batch_size
        self.batch_manager = batch_manager
        self.processor = processor
        self.cache_manager = cache_manager
        self.test_mode = test_mode
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def add_documents(self, documents: list[dict], deduplicate: bool = True) -> list[str]:
        """Add multiple documents to the storage system.

        Processes and adds a batch of documents to storage, with optional
        deduplication and caching. Handles validation and error cases.

        Args:
            documents: List of document dictionaries to add, each containing:
                - uuid: Document UUID
                - content: Document content
                - metadata: Document metadata
                - embeddings: Document embeddings
            deduplicate: Whether to check for and prevent duplicates (default: True).

        Returns:
            List[str]: List of successfully added document UUIDs.

        Raises:
            Exception: If document addition process fails.

        Example:
            ```python
            docs = [
                {
                    "uuid": "123e4567-e89b-12d3-a456-426614174000",
                    "content": {"body": "Document text"},
                    "metadata": {"title": "Doc Title"},
                    "embeddings": {"body": [0.1, 0.2]}
                }
            ]
            doc_ids = adder.add_documents(docs, deduplicate=True)
            ```
        """
        if not documents:
            self.logger.debug("No documents provided to add")
            return []

        self.logger.debug(f"Processing {len(documents)} documents (deduplicate={deduplicate})")

        # Try to get from cache first
        if self.cache_manager:
            cache_key = f"docs:{hash(str(documents))}"
            self.logger.debug(f"Checking cache with key: {cache_key}")
            cached_ids = self.cache_manager.get(cache_key)
            if cached_ids:
                self.logger.info(f"Retrieved {len(cached_ids)} document IDs from cache")
                return cached_ids

        try:
            doc_ids = self._add_documents_impl(documents, deduplicate)
            self.logger.info(f"Successfully added {len(doc_ids)} documents")

            # Cache the results
            if self.cache_manager:
                cache_key = f"docs:{hash(str(documents))}"
                self.logger.debug(f"Caching {len(doc_ids)} document IDs with key: {cache_key}")
                self.cache_manager.set(cache_key, doc_ids)

            return doc_ids
        except Exception as e:
            self.logger.error(f"Error adding documents: {e!s}", exc_info=True)
            raise

    def _add_documents_impl(self, documents: list[dict], deduplicate: bool) -> list[str]:
        """Internal implementation of document addition process.

        Handles the core logic of adding documents, including validation,
        deduplication, and batch processing.

        Args:
            documents: List of document dictionaries to process.
            deduplicate: Whether to perform deduplication.

        Returns:
            List[str]: List of successfully processed document UUIDs.

        Raises:
            Exception: If document processing fails.

        Note:
            This is an internal method and should not be called directly.
            Use add_documents() instead.
        """
        try:
            doc_ids = []
            seen_hashes: set[str] = set()

            for doc in documents:
                self.logger.debug(
                    f"Processing document: {doc.get('uuid', 'No UUID')} - {doc.get('metadata', {}).get('title', 'No title')}"
                )

                # Validate document first
                if not self.processor.validate_document(doc):
                    self.logger.error(
                        f"Document validation failed: {doc.get('metadata', {}).get('title', 'No title')}"
                    )
                    self.logger.debug(f"Invalid document structure: {doc}")
                    continue

                # Get document ID
                doc_id = doc.get("uuid")
                if not doc_id:
                    self.logger.error("Document missing UUID")
                    self.logger.debug(f"Document without UUID: {doc}")
                    continue

                try:
                    # Validate UUID format
                    doc_id = str(uuid.UUID(doc_id))
                except ValueError as ve:
                    self.logger.error(f"Invalid UUID format: {doc_id}")
                    self.logger.debug(f"UUID validation error: {ve!s}")
                    continue

                # Check for duplicates if deduplication is enabled
                if deduplicate:
                    doc_hash = self.processor.compute_document_hash(doc)
                    if doc_hash in seen_hashes:
                        self.logger.debug(f"Skipping duplicate document: {doc_id}")
                        continue
                    seen_hashes.add(doc_hash)

                # Process document
                try:
                    properties, vector = self.processor.prepare_document(doc)
                    self.logger.debug(
                        f"Prepared document {doc_id} with vector length: {len(vector) if vector else 'None'}"
                    )

                    # Add to batch
                    self.batch_manager.add_document(properties, vector, doc_id)
                    doc_ids.append(doc_id)
                    self.logger.debug(f"Successfully processed document {doc_id}")
                except Exception as e:
                    self.logger.error(
                        f"Error processing document {doc_id}: {e!s}", exc_info=True
                    )
                    continue

            return doc_ids
        except Exception as e:
            self.logger.error(f"Error in document addition: {e!s}", exc_info=True)
            raise

    def _process_batch(self, batch: list[tuple[dict, list[float], str]]) -> None:
        """Process a batch of prepared documents.

        Adds a batch of prepared documents to storage and updates the cache
        if enabled.

        Args:
            batch: List of tuples containing:
                - Dict: Document properties
                - List[float]: Document vector
                - str: Document UUID

        Raises:
            Exception: If batch processing fails.

        Note:
            This is an internal method and should not be called directly.
            Use add_documents() instead.
        """
        try:
            for properties, vector, doc_id in batch:
                self.batch_manager.add_document(properties, vector, doc_id)

                # Cache document if using caching
                if self.cache_manager:
                    self.cache_manager.set(f"doc:{doc_id}", properties)

            self.logger.info(f"Successfully processed batch of {len(batch)} documents")
        except Exception as e:
            self.logger.error(f"Error processing batch: {e!s}")
            raise
