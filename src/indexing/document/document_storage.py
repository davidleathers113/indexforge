"""Document storage operations module.

This module provides a high-level interface for document storage operations including
addition, deletion, and updates. It integrates with Weaviate for vector storage and
supports batch operations, caching, and document deduplication.
"""


import weaviate

from src.utils.cache_manager import CacheManager

from .batch_manager import BatchManager
from .document_processor import DocumentProcessor
from .operations.addition import DocumentAddition
from .operations.deletion import DocumentDeletion
from .operations.update import DocumentUpdate


class DocumentStorage:
    """Manages document storage operations in the vector database.

    This class provides a high-level interface for managing document operations
    in the vector database, including batch document additions, deletions, and
    updates. It coordinates between different operation handlers and manages
    caching and batch processing.

    Attributes:
        client (weaviate.Client): Weaviate client instance.
        class_name (str): Name of the document class in Weaviate.
        batch_size (int): Size of document batches for batch operations.
        cache_manager (Optional[CacheManager]): Manager for document caching.
        processor (DocumentProcessor): Processor for document operations.
        batch_manager (BatchManager): Manager for batch operations.
        addition (DocumentAddition): Handler for document addition operations.
        deletion (DocumentDeletion): Handler for document deletion operations.
        update (DocumentUpdate): Handler for document update operations.
    """

    def __init__(
        self,
        client: weaviate.Client,
        class_name: str,
        batch_size: int = 100,
        cache_manager: CacheManager | None = None,
        test_mode: bool = False,
    ):
        """Initialize document storage manager.

        Sets up the document storage manager with specified configuration and
        initializes all necessary components for document operations.

        Args:
            client: Weaviate client instance for database operations.
            class_name: Name of the document class in Weaviate.
            batch_size: Maximum number of documents per batch operation (default: 100).
            cache_manager: Optional cache manager for document caching.
            test_mode: Whether to run in test mode (default: False).

        Example:
            ```python
            client = weaviate.Client("http://localhost:8080")
            storage = DocumentStorage(
                client=client,
                class_name="Document",
                batch_size=100,
                cache_manager=cache_mgr
            )
            ```
        """
        self.client = client
        self.class_name = class_name
        self.batch_size = batch_size
        self.cache_manager = cache_manager

        # Initialize components
        self.processor = DocumentProcessor()
        self.batch_manager = BatchManager(client, class_name, batch_size, test_mode=test_mode)

        # Initialize operations
        self.addition = DocumentAddition(
            client,
            class_name,
            batch_size,
            self.batch_manager,
            self.processor,
            cache_manager,
            test_mode=test_mode,
        )
        self.deletion = DocumentDeletion(client, class_name, cache_manager, test_mode=test_mode)
        self.update = DocumentUpdate(client, class_name, self.processor, cache_manager)

    def add_documents(self, documents: list[dict], deduplicate: bool = True) -> list[str]:
        """Add multiple documents to storage.

        Processes and adds a batch of documents to the storage system, with optional
        deduplication to prevent duplicate entries.

        Args:
            documents: List of document dictionaries to add, each containing:
                - content: Document content
                - embeddings: Document embeddings
                - metadata: Document metadata
            deduplicate: Whether to check for and prevent duplicates (default: True).

        Returns:
            List[str]: List of assigned document IDs for the added documents.

        Example:
            ```python
            docs = [
                {
                    "content": {"body": "Document 1"},
                    "embeddings": {"body": [0.1, 0.2]},
                    "metadata": {"title": "Doc 1"}
                }
            ]
            doc_ids = storage.add_documents(docs, deduplicate=True)
            ```
        """
        return self.addition.add_documents(documents, deduplicate)

    def delete_documents(self, doc_ids: list[str]) -> bool:
        """Delete multiple documents from storage.

        Removes specified documents from the storage system and updates
        the cache accordingly.

        Args:
            doc_ids: List of document UUIDs to delete.

        Returns:
            bool: True if all deletions were successful, False otherwise.

        Example:
            ```python
            success = storage.delete_documents([
                "123e4567-e89b-12d3-a456-426614174000",
                "987fcdeb-51a2-43fe-ba98-765432198765"
            ])
            ```
        """
        return self.deletion.delete_documents(doc_ids)

    def update_document(
        self, doc_id: str, updates: dict, vector: list[float] | None = None
    ) -> bool:
        """Update a single document in storage.

        Updates the properties and optionally the vector representation of a
        document in the storage system.

        Args:
            doc_id: UUID of the document to update.
            updates: Dictionary of document properties to update.
            vector: Optional new vector representation for the document.

        Returns:
            bool: True if update was successful, False otherwise.

        Example:
            ```python
            success = storage.update_document(
                doc_id="123e4567-e89b-12d3-a456-426614174000",
                updates={"metadata": {"title": "Updated Title"}},
                vector=[0.1, 0.2, 0.3]
            )
            ```
        """
        return self.update.update_document(doc_id, updates, vector)
