"""Storage management for document lineage data.

This module provides functionality for persisting and retrieving document lineage data,
handling serialization and deserialization of complex data structures, and managing
the storage directory structure.

The storage system uses JSON files to store document lineage information, with automatic
handling of datetime serialization and custom object types. It provides atomic operations
for reading and writing data to prevent corruption during concurrent access.

Key Features:
    - Document lineage persistence
    - Atomic file operations
    - Custom type serialization
    - Thread-safe operations
    - Query capabilities
    - Backup support

Example:
    ```python
    from datetime import datetime, timedelta
    from src.core.storage.tracking import LineageStorage
    from src.core.models.lineage import DocumentLineage

    # Initialize storage
    storage = LineageStorage("/path/to/storage")

    # Store document lineage
    lineage = DocumentLineage(doc_id="doc123")
    storage.save_lineage(lineage)

    # Query documents
    recent_docs = storage.get_lineages_by_time(
        start_time=datetime.now() - timedelta(days=1)
    )
    ```
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
import json
import logging
from pathlib import Path
import threading

from src.core.models.lineage import DocumentLineage
from src.core.processing.steps.models.step import ProcessingStatus


logger = logging.getLogger(__name__)


class LineageStorageError(Exception):
    """Base exception for lineage storage errors."""


class StorageAccessError(LineageStorageError):
    """Error accessing storage location."""


class DataCorruptionError(LineageStorageError):
    """Error with data integrity."""


class LineageStorageBase(ABC):
    """Abstract base class defining the interface for lineage storage."""

    @abstractmethod
    def get_lineage(self, doc_id: str) -> DocumentLineage | None:
        """Get document lineage by ID."""
        pass

    @abstractmethod
    def save_lineage(self, lineage: DocumentLineage) -> None:
        """Save document lineage."""
        pass

    @abstractmethod
    def get_all_lineages(self) -> dict[str, DocumentLineage]:
        """Get all document lineages."""
        pass

    @abstractmethod
    def delete_lineage(self, doc_id: str) -> None:
        """Delete document lineage."""
        pass

    @abstractmethod
    def get_lineages_by_time(
        self, start_time: datetime | None = None, end_time: datetime | None = None
    ) -> dict[str, DocumentLineage]:
        """Get document lineages within a time range."""
        pass


class LineageStorage(LineageStorageBase):
    """Implementation of document lineage storage."""

    def __init__(self, storage_dir: str | Path):
        """Initialize lineage storage.

        Args:
            storage_dir: Path to storage directory.
        """
        self.storage_dir = Path(storage_dir)
        self._data: dict[str, DocumentLineage] = {}
        self._lock = threading.Lock()
        self._last_save = datetime.min.replace(tzinfo=UTC)
        self._modified = False
        self._initialize_storage()

    def _initialize_storage(self) -> None:
        """Initialize storage directory and load data."""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self._load_data()
        except Exception as e:
            logger.error(f"Failed to initialize storage: {e}")
            raise StorageAccessError(f"Storage initialization failed: {e}") from e

    def _load_data(self) -> None:
        """Load lineage data from storage."""
        data_file = self.storage_dir / "lineage_data.json"
        if not data_file.exists():
            return

        try:
            with data_file.open("r") as f:
                raw_data = json.load(f)

            with self._lock:
                self._data = {
                    doc_id: DocumentLineage.from_dict(data) for doc_id, data in raw_data.items()
                }
                self._last_save = datetime.now(UTC)

        except json.JSONDecodeError as e:
            logger.error(f"Data corruption detected: {e}")
            raise DataCorruptionError(f"Failed to decode lineage data: {e}") from e
        except Exception as e:
            logger.error(f"Error loading lineage data: {e}")
            raise StorageAccessError(f"Failed to load lineage data: {e}") from e

    def _save_data(self) -> None:
        """Save lineage data to storage."""
        if not self._modified:
            return

        data_file = self.storage_dir / "lineage_data.json"
        temp_file = data_file.with_suffix(".tmp")

        try:
            # Prepare data for serialization
            with self._lock:
                serialized_data = {
                    doc_id: lineage.to_dict() for doc_id, lineage in self._data.items()
                }

            # Write to temporary file first
            with temp_file.open("w") as f:
                json.dump(serialized_data, f, indent=2, default=str)

            # Atomic rename
            temp_file.replace(data_file)

            with self._lock:
                self._last_save = datetime.now(UTC)
                self._modified = False

        except Exception as e:
            logger.error(f"Error saving lineage data: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise StorageAccessError(f"Failed to save lineage data: {e}") from e

    def get_lineage(self, doc_id: str) -> DocumentLineage | None:
        """Get document lineage by ID.

        Args:
            doc_id: Document ID to retrieve.

        Returns:
            DocumentLineage if found, None otherwise.
        """
        with self._lock:
            return self._data.get(doc_id)

    def save_lineage(self, lineage: DocumentLineage) -> None:
        """Save document lineage.

        Args:
            lineage: DocumentLineage to save.
        """
        with self._lock:
            self._data[lineage.doc_id] = lineage
            self._modified = True
        self._save_data()

    def get_all_lineages(self) -> dict[str, DocumentLineage]:
        """Get all document lineages.

        Returns:
            Dictionary mapping document IDs to their lineage data.
        """
        with self._lock:
            return self._data.copy()

    def delete_lineage(self, doc_id: str) -> None:
        """Delete document lineage.

        Args:
            doc_id: Document ID to delete.
        """
        with self._lock:
            if doc_id in self._data:
                del self._data[doc_id]
                self._modified = True
        self._save_data()

    def get_lineages_by_time(
        self, start_time: datetime | None = None, end_time: datetime | None = None
    ) -> dict[str, DocumentLineage]:
        """Get document lineages within a time range.

        Args:
            start_time: Start of time range (inclusive).
            end_time: End of time range (inclusive).

        Returns:
            Dictionary of document lineages within the time range.
        """
        with self._lock:
            filtered = {}
            for doc_id, lineage in self._data.items():
                if not lineage.processing_steps:
                    continue

                latest_step = max(lineage.processing_steps, key=lambda x: x.timestamp)
                if start_time and latest_step.timestamp < start_time:
                    continue
                if end_time and latest_step.timestamp > end_time:
                    continue
                filtered[doc_id] = lineage

            return filtered

    def get_lineages_by_status(self, status: ProcessingStatus) -> dict[str, DocumentLineage]:
        """Get document lineages by processing status.

        Args:
            status: Processing status to filter by.

        Returns:
            Dictionary of document lineages with the specified status.
        """
        with self._lock:
            filtered = {}
            for doc_id, lineage in self._data.items():
                if not lineage.processing_steps:
                    continue

                latest_step = max(lineage.processing_steps, key=lambda x: x.timestamp)
                if latest_step.status == status:
                    filtered[doc_id] = lineage

            return filtered

    def __len__(self) -> int:
        """Get number of stored lineages."""
        with self._lock:
            return len(self._data)

    def __contains__(self, doc_id: str) -> bool:
        """Check if document ID exists in storage."""
        with self._lock:
            return doc_id in self._data

    def __iter__(self):
        """Iterate over document IDs."""
        with self._lock:
            return iter(self._data.keys())

    def items(self):
        """Get items iterator."""
        with self._lock:
            return self._data.copy().items()

    def values(self):
        """Get values iterator."""
        with self._lock:
            return self._data.copy().values()

    def keys(self):
        """Get keys iterator."""
        with self._lock:
            return self._data.copy().keys()
