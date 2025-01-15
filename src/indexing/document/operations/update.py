"""Document update operations module for managing document updates in the storage system.

This module provides functionality for updating existing documents in the storage system,
handling both metadata updates and vector updates while maintaining cache consistency.
"""

import logging
from typing import Dict, List, Optional
import uuid

import weaviate

from src.indexing.document.document_processor import DocumentProcessor
from src.utils.cache_manager import CacheManager


class DocumentUpdate:
    """Handles document update operations in the storage system.

    This class provides methods for updating existing documents in the storage system,
    including their properties and vector representations. It handles UUID validation,
    property formatting, and cache management.

    Attributes:
        client (weaviate.Client): The Weaviate client instance for database operations.
        class_name (str): The name of the document class in Weaviate.
        processor (DocumentProcessor): Instance for processing document updates.
        cache_manager (Optional[CacheManager]): Manager for document cache operations.
        test_mode (bool): Flag indicating if running in test mode.
        logger (logging.Logger): Logger instance for this class.
    """

    def __init__(
        self,
        client: weaviate.Client,
        class_name: str,
        processor: DocumentProcessor,
        cache_manager: Optional[CacheManager] = None,
        test_mode: bool = False,
    ):
        """Initialize document update handler.

        Args:
            client: Weaviate client instance for database operations.
            class_name: Name of the document class in Weaviate.
            processor: Document processor instance for handling updates.
            cache_manager: Optional cache manager for document caching.
            test_mode: Whether running in test mode (default: False).

        Example:
            ```python
            client = weaviate.Client("http://localhost:8080")
            updater = DocumentUpdate(
                client=client,
                class_name="Document",
                processor=doc_processor,
                cache_manager=cache_mgr
            )
            ```
        """
        self.client = client
        self.class_name = class_name
        self.processor = processor
        self.cache_manager = cache_manager
        self.test_mode = test_mode
        self.logger = logging.getLogger(__name__)

    def update_document(
        self, doc_id: str, updates: Dict, vector: Optional[List[float]] = None
    ) -> bool:
        """Update an existing document in storage.

        Updates both document properties and optionally its vector representation.
        Handles string-to-list conversion as required by Weaviate and manages cache invalidation.

        Args:
            doc_id: UUID string of the document to update.
            updates: Dictionary containing the document property updates.
            vector: Optional new vector representation for the document.

        Returns:
            bool: True if update was successful, False otherwise.

        Raises:
            ValueError: If the document ID is not a valid UUID.
            Exception: For any other errors during the update process.

        Example:
            ```python
            success = updater.update_document(
                doc_id="123e4567-e89b-12d3-a456-426614174000",
                updates={"title": "Updated Title", "content": "New content"},
                vector=[0.1, 0.2, 0.3]
            )
            ```
        """
        try:
            # Validate UUID format
            try:
                uuid_obj = uuid.UUID(doc_id)
            except ValueError as ve:
                self.logger.error(f"Invalid UUID format for document {doc_id}: {str(ve)}")
                return False

            # Prepare update properties
            properties = {}
            for key, value in updates.items():
                if isinstance(value, str):
                    # Convert string values to lists as required by Weaviate
                    properties[key] = [value]
                else:
                    properties[key] = value

            # Update document
            result = self.client.data_object.update(
                uuid_str=str(uuid_obj),
                class_name=self.class_name,
                data_object=properties,
                vector=vector,
            )

            # Weaviate returns None on successful update
            if result is not None:
                self.logger.error(f"Unexpected response from update operation: {result}")
                return False

            # Clear cache if using caching
            if self.cache_manager:
                self.cache_manager.delete(f"doc:{doc_id}")

            return True
        except Exception as e:
            self.logger.error(f"Error updating document {doc_id}: {str(e)}")
            return False
