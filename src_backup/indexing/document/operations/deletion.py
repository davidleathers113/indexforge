"""Document deletion operations module.

This module provides functionality for deleting documents from the storage system,
including UUID validation, cache management, and error handling. It handles both
single and batch document deletions with detailed logging and status reporting.
"""

import logging
import uuid

import weaviate
from weaviate.exceptions import UnexpectedStatusCodeException

from src.utils.cache_manager import CacheManager


class DocumentDeletion:
    """Handles document deletion operations in the storage system.

    This class manages the deletion of documents from the storage system,
    including UUID validation, cache invalidation, and error handling.
    It provides detailed logging of the deletion process and handles
    various edge cases like non-existent documents.

    Attributes:
        client (weaviate.Client): Weaviate client instance for database operations.
        class_name (str): Name of the document class in Weaviate.
        cache_manager (Optional[CacheManager]): Manager for document caching.
        test_mode (bool): Whether running in test mode.
        logger (logging.Logger): Logger instance for this class.
    """

    def __init__(
        self,
        client: weaviate.Client,
        class_name: str,
        cache_manager: CacheManager | None = None,
        test_mode: bool = False,
    ):
        """Initialize the document deletion handler.

        Sets up the document deletion handler with the specified configuration
        and initializes logging.

        Args:
            client: Weaviate client instance for database operations.
            class_name: Name of the document class in Weaviate.
            cache_manager: Optional cache manager for document caching.
            test_mode: Whether to run in test mode (default: False).

        Example:
            ```python
            client = weaviate.Client("http://localhost:8080")
            deleter = DocumentDeletion(
                client=client,
                class_name="Document",
                cache_manager=cache_mgr
            )
            ```
        """
        self.client = client
        self.class_name = class_name
        self.cache_manager = cache_manager
        self.test_mode = test_mode
        self.logger = logging.getLogger(__name__)

    def delete_documents(self, doc_ids: list[str]) -> bool:
        """Delete multiple documents from the storage system.

        Processes a list of document IDs for deletion, validating each UUID
        and handling cache invalidation. Continues processing even if some
        deletions fail, but returns False if any deletion fails.

        Args:
            doc_ids: List of document UUIDs to delete.

        Returns:
            bool: True if all deletions were successful, False if any failed.

        Raises:
            ValueError: If any document ID is not a valid UUID.
            UnexpectedStatusCodeException: If Weaviate returns unexpected status.
            Exception: For any other errors during deletion.

        Example:
            ```python
            success = deleter.delete_documents([
                "123e4567-e89b-12d3-a456-426614174000",
                "987fcdeb-51a2-43fe-ba98-765432198765"
            ])
            if success:
                print("All documents deleted successfully")
            ```

        Note:
            - Returns True if no documents are provided to delete
            - Skips non-existent documents with a warning
            - Clears cache entries for successfully deleted documents
        """
        try:
            if not doc_ids:
                self.logger.info("No documents to delete")
                return True

            self.logger.info(f"Starting deletion of {len(doc_ids)} documents")
            for doc_id in doc_ids:
                try:
                    self.logger.debug(f"Attempting to validate UUID format for {doc_id}")
                    # Validate UUID format
                    uuid_obj = uuid.UUID(doc_id)
                    self.logger.debug(f"UUID validation successful for {doc_id}")

                    self.logger.debug(f"Calling delete on client for {doc_id}")
                    result = self.client.data_object.delete(
                        str(uuid_obj), class_name=self.class_name
                    )
                    self.logger.debug(f"Delete call completed for {doc_id} with result: {result}")

                    # Weaviate returns None on successful deletion
                    if result is not None:
                        self.logger.error(f"Unexpected response from delete operation: {result}")
                        return False

                    # Clear cache if using caching
                    if self.cache_manager:
                        self.logger.debug(f"Clearing cache for {doc_id}")
                        self.cache_manager.delete(f"doc:{doc_id}")
                except ValueError as ve:
                    self.logger.error(f"Invalid UUID format for document {doc_id}: {ve!s}")
                    return False
                except UnexpectedStatusCodeException as e:
                    if "404" in str(e):
                        self.logger.warning(f"Document {doc_id} not found, skipping")
                        continue
                    self.logger.error(f"Error deleting document {doc_id}: {e!s}")
                    return False
                except Exception as e:
                    self.logger.error(f"Error deleting document {doc_id}: {e!s}")
                    return False
            self.logger.info("Document deletion completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting documents: {e!s}")
            return False
