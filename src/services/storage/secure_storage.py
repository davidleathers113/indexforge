"""Secure storage wrapper implementation.

This module provides a secure storage wrapper that integrates encryption
with storage operations, ensuring data is encrypted at rest.
"""

import logging
from pathlib import Path
from typing import Generic, TypeVar
from uuid import UUID

from src.core.interfaces.storage import DocumentStorage
from src.core.models.documents import Document
from src.core.security.encryption import EncryptionManager
from src.core.settings import Settings

from .secure_metadata import MetadataHandler, SecureStorageMetadata

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=Document)


class SecureStorageWrapper(Generic[T]):
    """Wrapper that adds encryption to storage operations."""

    def __init__(
        self,
        storage: DocumentStorage[T],
        encryption_manager: EncryptionManager,
        settings: Settings,
        metadata_dir: Path | None = None,
    ) -> None:
        """Initialize secure storage wrapper.

        Args:
            storage: Base storage implementation to wrap
            encryption_manager: Encryption manager for data protection
            settings: Application settings
            metadata_dir: Optional directory for storing metadata
        """
        self._storage = storage
        self._encryption = encryption_manager
        self._settings = settings
        self._metadata = MetadataHandler(metadata_dir or Path("data/secure_storage/metadata"))

    async def store_document(self, document: T) -> UUID:
        """Store a document securely.

        Args:
            document: Document to store

        Returns:
            UUID: Generated document ID

        Raises:
            ValueError: If document is invalid
            StorageError: If storage operation fails
            EncryptionError: If encryption fails
        """
        if not document:
            raise ValueError("Document cannot be None")

        try:
            # Encrypt document
            document_bytes = document.json().encode()
            encrypted_data = await self._encryption.encrypt(document_bytes)

            # Store document and metadata
            doc_id = await self._storage.store_document(document)
            metadata = SecureStorageMetadata(encryption_data=encrypted_data)
            self._metadata.save(doc_id, metadata)
            return doc_id
        except Exception as e:
            logger.error(f"Failed to store document securely: {e}")
            raise

    async def get_document(self, document_id: UUID) -> T | None:
        """Retrieve and decrypt a document.

        Args:
            document_id: ID of document to retrieve

        Returns:
            Optional[T]: Decrypted document if found

        Raises:
            StorageError: If storage operation fails
            EncryptionError: If decryption fails
        """
        metadata = self._metadata.get(document_id)
        if not metadata:
            return None

        try:
            document = await self._storage.get_document(document_id)
            if not document:
                return None

            # Decrypt document
            document_bytes = await self._encryption.decrypt(metadata.encryption_data)
            return Document.parse_raw(document_bytes.decode())
        except Exception as e:
            logger.error(f"Failed to retrieve document {document_id}: {e}")
            raise

    async def delete_document(self, document_id: UUID) -> None:
        """Delete a document and its metadata.

        Args:
            document_id: ID of document to delete

        Raises:
            StorageError: If storage operation fails
        """
        try:
            await self._storage.delete_document(document_id)
            self._metadata.delete(document_id)
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise
