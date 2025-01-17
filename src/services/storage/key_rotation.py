"""Key rotation handler for secure storage.

This module handles the re-encryption of documents when encryption keys are rotated.
"""

import logging
from typing import TypeVar
from uuid import UUID

from src.core.models.documents import Document
from src.core.security.encryption import EncryptionManager

from .secure_storage import SecureStorageWrapper

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=Document)


class KeyRotationHandler:
    """Handles re-encryption of documents during key rotation."""

    def __init__(self, storage: SecureStorageWrapper[T], encryption: EncryptionManager) -> None:
        """Initialize key rotation handler.

        Args:
            storage: Secure storage wrapper instance
            encryption: Encryption manager for key rotation
        """
        self._storage = storage
        self._encryption = encryption

    async def rotate_keys(self, doc_ids: list[UUID]) -> tuple[list[UUID], list[UUID]]:
        """Rotate encryption keys and re-encrypt documents.

        Args:
            doc_ids: List of document IDs to re-encrypt

        Returns:
            Tuple containing:
                - List of successfully re-encrypted document IDs
                - List of failed document IDs
        """
        # Rotate encryption keys
        await self._encryption.rotate_keys()

        successful_ids = []
        failed_ids = []

        # Re-encrypt each document
        for doc_id in doc_ids:
            try:
                document = await self._storage.get_document(doc_id)
                if document:
                    await self._storage.store_document(document)
                    successful_ids.append(doc_id)
                else:
                    failed_ids.append(doc_id)
            except Exception as e:
                logger.error(f"Failed to re-encrypt document {doc_id}: {e}")
                failed_ids.append(doc_id)

        return successful_ids, failed_ids
