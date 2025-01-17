"""Mock implementations for testing document tracking."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.core.models import DocumentLineage

logger = logging.getLogger(__name__)


class MockLineageStorage:
    """Mock implementation of LineageStorage for testing."""

    def __init__(self, storage_dir: str) -> None:
        """Initialize mock storage.

        Args:
            storage_dir: Directory to store lineage data
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._lineage_data: Dict[str, DocumentLineage] = {}
        logger.debug("Initialized mock storage in directory: %s", storage_dir)

    @property
    def lineage_data(self) -> Dict[str, DocumentLineage]:
        """Get the current lineage data."""
        # Load all files from storage into memory
        for file_path in self.storage_dir.glob("*.json"):
            doc_id = file_path.stem
            if doc_id not in self._lineage_data:
                with file_path.open("r") as f:
                    data = json.load(f)
                    self._lineage_data[doc_id] = DocumentLineage.from_dict(data)
        return self._lineage_data

    def _get_file_path(self, doc_id: str) -> Path:
        """Get the file path for a document's lineage data.

        Args:
            doc_id: Document ID

        Returns:
            Path: File path for the document's lineage data
        """
        return self.storage_dir / f"{doc_id}.json"

    def get_lineage(self, doc_id: str) -> Optional[DocumentLineage]:
        """Retrieve lineage information for a document.

        Args:
            doc_id: ID of the document to retrieve

        Returns:
            DocumentLineage if found, None otherwise
        """
        file_path = self._get_file_path(doc_id)
        if not file_path.exists():
            logger.debug("No lineage found for document: %s", doc_id)
            return None

        try:
            with file_path.open("r") as f:
                data = json.load(f)
            logger.debug("Retrieved lineage for document: %s", doc_id)
            lineage = DocumentLineage.from_dict(data)
            self._lineage_data[doc_id] = lineage
            return lineage
        except Exception as e:
            logger.error("Error retrieving lineage for document %s: %s", doc_id, str(e))
            raise

    def save_lineage(self, lineage: DocumentLineage) -> None:
        """Save lineage information for a document.

        Args:
            lineage: The document lineage to save
        """
        file_path = self._get_file_path(lineage.doc_id)
        try:
            with file_path.open("w") as f:
                json.dump(lineage.to_dict(), f, indent=2)
            self._lineage_data[lineage.doc_id] = lineage
            logger.debug("Saved lineage for document: %s", lineage.doc_id)
        except Exception as e:
            logger.error("Error saving lineage for document %s: %s", lineage.doc_id, str(e))
            raise

    def delete_lineage(self, doc_id: str) -> None:
        """Delete lineage information for a document.

        Args:
            doc_id: ID of the document to delete
        """
        file_path = self._get_file_path(doc_id)
        try:
            if file_path.exists():
                file_path.unlink()
                self._lineage_data.pop(doc_id, None)
                logger.debug("Deleted lineage for document: %s", doc_id)
            else:
                logger.debug("No lineage found to delete for document: %s", doc_id)
        except Exception as e:
            logger.error("Error deleting lineage for document %s: %s", doc_id, str(e))
            raise

    def get_all_lineage(self) -> List[DocumentLineage]:
        """Get all document lineage records.

        Returns:
            List[DocumentLineage]: List of all document lineage records
        """
        return list(self.lineage_data.values())

    def update_document_lineage(self, doc_id: str, updates: Dict) -> None:
        """Update specific fields in a document's lineage.

        Args:
            doc_id: ID of the document to update
            updates: Dictionary of fields to update
        """
        lineage = self.get_lineage(doc_id)
        if lineage is None:
            raise ValueError(f"Document {doc_id} not found")

        for key, value in updates.items():
            setattr(lineage, key, value)

        self.save_lineage(lineage)
