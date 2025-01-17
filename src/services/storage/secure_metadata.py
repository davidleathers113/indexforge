"""Secure storage metadata handler.

This module handles the persistence and management of encryption metadata
for securely stored documents.
"""

import json
import logging
from pathlib import Path
from typing import Dict
from uuid import UUID

from pydantic import BaseModel

from src.core.security.encryption import EncryptedData

logger = logging.getLogger(__name__)


class SecureStorageMetadata(BaseModel):
    """Metadata for securely stored items."""

    version: int = 1
    encryption_data: EncryptedData


class MetadataHandler:
    """Handles persistence of secure storage metadata."""

    def __init__(self, metadata_dir: Path) -> None:
        """Initialize metadata handler.

        Args:
            metadata_dir: Directory for storing metadata files
        """
        self._metadata_dir = metadata_dir
        self._metadata: Dict[UUID, SecureStorageMetadata] = {}
        self._metadata_dir.mkdir(parents=True, exist_ok=True)
        self._load_all()

    def _get_path(self, doc_id: UUID) -> Path:
        """Get metadata file path for document.

        Args:
            doc_id: Document ID

        Returns:
            Path to metadata file
        """
        return self._metadata_dir / f"{doc_id}.meta.json"

    def _load_all(self) -> None:
        """Load all metadata from disk."""
        for metadata_file in self._metadata_dir.glob("*.meta.json"):
            try:
                doc_id = UUID(metadata_file.stem.split(".")[0])
                with metadata_file.open("r") as f:
                    metadata_dict = json.load(f)
                    self._metadata[doc_id] = SecureStorageMetadata.parse_obj(metadata_dict)
            except Exception as e:
                logger.error(f"Failed to load metadata from {metadata_file}: {e}")

    def get(self, doc_id: UUID) -> SecureStorageMetadata | None:
        """Get metadata for document.

        Args:
            doc_id: Document ID

        Returns:
            Metadata if found, None otherwise
        """
        return self._metadata.get(doc_id)

    def save(self, doc_id: UUID, metadata: SecureStorageMetadata) -> None:
        """Save metadata for document.

        Args:
            doc_id: Document ID
            metadata: Metadata to save
        """
        path = self._get_path(doc_id)
        temp_path = path.with_suffix(".tmp")
        try:
            with temp_path.open("w") as f:
                json.dump(metadata.dict(), f)
            temp_path.replace(path)
            self._metadata[doc_id] = metadata
        except Exception as e:
            logger.error(f"Failed to save metadata for {doc_id}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise

    def delete(self, doc_id: UUID) -> None:
        """Delete metadata for document.

        Args:
            doc_id: Document ID
        """
        path = self._get_path(doc_id)
        try:
            path.unlink(missing_ok=True)
            self._metadata.pop(doc_id, None)
        except Exception as e:
            logger.error(f"Failed to delete metadata for {doc_id}: {e}")
            raise
