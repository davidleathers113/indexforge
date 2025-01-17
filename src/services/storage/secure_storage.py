"""Secure storage wrapper implementation.

This module provides a secure storage wrapper that integrates encryption
with storage operations, ensuring data is encrypted at rest.
"""

import json
from pathlib import Path
from typing import Dict, Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel

from src.core.interfaces.storage import DocumentStorage
from src.core.models.documents import Document
from src.core.security.encryption import EncryptedData, EncryptionManager
from src.core.settings import Settings

T = TypeVar("T", bound=Document)


class SecureStorageMetadata(BaseModel):
    """Metadata for securely stored items."""

    version: int = 1
    encryption_data: EncryptedData


class SecureStorageWrapper(Generic[T]):
    """Wrapper that adds encryption to storage operations."""

    def __init__(
        self,
        storage: DocumentStorage[T],
        encryption_manager: EncryptionManager,
        settings: Settings,
        metadata_dir: Optional[Path] = None,
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
        self._metadata: Dict[UUID, SecureStorageMetadata] = {}
        self._metadata_dir = metadata_dir or Path("data/secure_storage/metadata")
        self._metadata_dir.mkdir(parents=True, exist_ok=True)
        self._load_metadata()

    def _get_metadata_path(self, doc_id: UUID) -> Path:
        """Get path for document metadata file.

        Args:
            doc_id: Document ID

        Returns:
            Path to metadata file
        """
        return self._metadata_dir / f"{doc_id}.json"

    def _load_metadata(self) -> None:
        """Load metadata from disk."""
        for metadata_file in self._metadata_dir.glob("*.json"):
            try:
                doc_id = UUID(metadata_file.stem)
                with metadata_file.open("r") as f:
                    metadata_dict = json.load(f)
                    self._metadata[doc_id] = SecureStorageMetadata.parse_obj(metadata_dict)
            except Exception:
                # Log error but continue loading other files
                continue

    def _save_metadata(self, doc_id: UUID, metadata: SecureStorageMetadata) -> None:
        """Save metadata to disk.

        Args:
            doc_id: Document ID
            metadata: Metadata to save
        """
        metadata_path = self._get_metadata_path(doc_id)
        metadata_dict = metadata.dict()

        # Write atomically using temporary file
        temp_path = metadata_path.with_suffix(".tmp")
        with temp_path.open("w") as f:
            json.dump(metadata_dict, f)
        temp_path.replace(metadata_path)

    async def store_document(self, document: T) -> UUID:
        """Store a document securely.

        Args:
            document: Document to store

        Returns:
            UUID: Generated document ID
        """
        # Serialize and encrypt document
        document_bytes = document.json().encode()
        encrypted_data = await self._encryption.encrypt(document_bytes)

        # Store document and metadata
        doc_id = self._storage.store_document(document)
        metadata = SecureStorageMetadata(encryption_data=encrypted_data)
        self._metadata[doc_id] = metadata
        self._save_metadata(doc_id, metadata)

        return doc_id

    async def get_document(self, document_id: UUID) -> Optional[T]:
        """Retrieve and decrypt a document.

        Args:
            document_id: ID of document to retrieve

        Returns:
            Optional[T]: Decrypted document if found
        """
        metadata = self._metadata.get(document_id)
        if not metadata:
            return None

        # Retrieve and decrypt document
        encrypted_data = metadata.encryption_data
        document_bytes = await self._encryption.decrypt(encrypted_data)
        document = Document.parse_raw(document_bytes.decode())

        return document

    async def update_document(self, document_id: UUID, document: T) -> None:
        """Update a document securely.

        Args:
            document_id: ID of document to update
            document: Updated document
        """
        # Encrypt updated document
        document_bytes = document.json().encode()
        encrypted_data = await self._encryption.encrypt(document_bytes)

        # Update storage and metadata
        self._storage.update_document(document_id, document)
        metadata = SecureStorageMetadata(encryption_data=encrypted_data)
        self._metadata[document_id] = metadata
        self._save_metadata(document_id, metadata)

    async def delete_document(self, document_id: UUID) -> None:
        """Delete a document and its metadata.

        Args:
            document_id: ID of document to delete
        """
        self._storage.delete_document(document_id)
        self._metadata.pop(document_id, None)
        metadata_path = self._get_metadata_path(document_id)
        try:
            metadata_path.unlink()
        except FileNotFoundError:
            pass

    async def rotate_keys(self) -> None:
        """Rotate encryption keys and re-encrypt all documents."""
        # Rotate encryption keys
        await self._encryption.rotate_keys()

        # Re-encrypt all documents with new key
        for doc_id, metadata in list(self._metadata.items()):
            if document := await self.get_document(doc_id):
                await self.update_document(doc_id, document)
