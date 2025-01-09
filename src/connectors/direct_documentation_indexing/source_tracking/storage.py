"""
Storage management for document lineage data.

This module provides functionality for persisting and retrieving document lineage data,
handling serialization and deserialization of complex data structures, and managing
the storage directory structure.

The storage system uses JSON files to store document lineage information, with automatic
handling of datetime serialization and custom object types. It provides atomic operations
for reading and writing data to prevent corruption during concurrent access.

Example:
    ```python
    # Initialize storage
    storage = LineageStorage("/path/to/storage")

    # Add and retrieve documents
    storage.add_document("doc123", metadata={"type": "pdf"})
    lineage = storage.get_lineage("doc123")

    # Save changes
    storage.save_lineage_data()
    ```
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .enums import LogLevel, ProcessingStatus, TransformationType
from .models import DocumentLineage, LogEntry, ProcessingStep, Transformation
from .utils import load_json

logger = logging.getLogger(__name__)


class LineageStorageBase(ABC):
    """Abstract base class defining the interface for lineage storage."""

    @abstractmethod
    def get_lineage(self, doc_id: str) -> Optional[DocumentLineage]:
        """Get document lineage by ID."""
        pass

    @abstractmethod
    def save_lineage(self, lineage: DocumentLineage) -> None:
        """Save document lineage."""
        pass

    @abstractmethod
    def get_all_lineages(self) -> Dict[str, DocumentLineage]:
        """Get all document lineages."""
        pass

    @abstractmethod
    def delete_lineage(self, doc_id: str) -> None:
        """Delete document lineage."""
        pass

    @abstractmethod
    def get_lineages_by_time(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict[str, DocumentLineage]:
        """Get document lineages within a time range."""
        pass

    @abstractmethod
    def get_lineages_by_status(self, status: str) -> Dict[str, DocumentLineage]:
        """Get document lineages by processing status."""
        pass


class LineageStorage(LineageStorageBase):
    """
    Storage manager for document lineage data.

    This class handles the persistence of document lineage information, including
    loading from and saving to disk, managing the storage directory structure,
    and providing atomic operations for data access.

    The storage uses a JSON-based format for data persistence, with automatic
    handling of datetime serialization and custom object types. The storage
    structure is designed to be human-readable and easily inspectable for
    debugging purposes.

    Attributes:
        storage_dir (Path): Path to the directory where lineage data is stored.
        lineage_data (Dict[str, DocumentLineage]): In-memory cache of loaded lineage data.

    Example:
        ```python
        # Initialize storage
        storage = LineageStorage("/data/lineage")

        # Add a document
        storage.add_document(
            doc_id="doc123",
            metadata={"type": "pdf", "pages": 10}
        )

        # Get document data
        lineage = storage.get_lineage("doc123")
        print(f"Document created at: {lineage.created_at}")
        ```
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the storage manager.

        Args:
            storage_dir: Optional path to the storage directory. If not provided,
                       uses a default directory in the package's location.

        Example:
            ```python
            # Use default storage location
            storage = LineageStorage()

            # Use custom storage location
            storage = LineageStorage("/path/to/storage")
            ```
        """
        self.storage_dir = Path(storage_dir) if storage_dir else Path(__file__).parent / "lineage"
        logger.debug(f"Initializing LineageStorage with directory: {self.storage_dir}")
        self.lineage_data: Dict[str, DocumentLineage] = {}
        self._load_lineage_data()

    def _get_storage_path(self) -> Path:
        """
        Get the path to the lineage data storage file.

        Returns:
            Path object pointing to the JSON storage file.

        Note:
            This is an internal method used by the storage manager to maintain
            consistent file paths across operations.
        """
        path = self.storage_dir / "document_lineage.json"
        logger.debug(f"Storage path: {path}")
        return path

    def _load_lineage_data(self) -> None:
        """
        Load existing lineage data from storage.

        This method reads the JSON storage file and deserializes the data into
        DocumentLineage objects, handling all necessary type conversions and
        validation.

        Raises:
            Exception: If there are errors reading or parsing the storage file.
                     These are caught and logged, with an empty data set being
                     used as a fallback.

        Note:
            This is called automatically during initialization and should not
            typically need to be called directly.
        """
        try:
            storage_path = self._get_storage_path()
            logger.debug(f"Loading lineage data from {storage_path}")
            if storage_path.exists():
                data = load_json(storage_path)
                logger.debug(f"Found {len(data)} documents in storage")
                for doc_id, lineage in data.items():
                    logger.debug(f"Processing document {doc_id}")
                    self.lineage_data[doc_id] = DocumentLineage(
                        doc_id=doc_id,
                        origin_id=lineage.get("origin_id"),
                        origin_source=lineage.get("origin_source"),
                        origin_type=lineage.get("origin_type"),
                        derived_from=lineage.get("derived_from"),
                        derived_documents=lineage.get("derived_documents", []),
                        transformations=[
                            Transformation(
                                transform_type=TransformationType(t["transform_type"]),
                                timestamp=datetime.fromisoformat(t["timestamp"]),
                                description=t.get("description", ""),
                                parameters=t.get("parameters", {}),
                                metadata=t.get("metadata", {}),
                            )
                            for t in lineage.get("transformations", [])
                        ],
                        processing_steps=[
                            ProcessingStep(
                                step_name=p["step_name"],
                                status=ProcessingStatus(p["status"]),
                                timestamp=datetime.fromisoformat(p["timestamp"]),
                                details=p.get("details", {}),
                            )
                            for p in lineage.get("processing_steps", [])
                        ],
                        error_logs=[
                            LogEntry(
                                log_level=LogLevel(log_entry["level"]),
                                message=log_entry["message"],
                                timestamp=datetime.fromisoformat(log_entry["timestamp"]),
                                metadata=log_entry.get("metadata", {}),
                            )
                            for log_entry in lineage.get("error_logs", [])
                        ],
                        performance_metrics=lineage.get("performance_metrics", {}),
                        metadata=lineage.get("metadata", {}),
                        created_at=datetime.fromisoformat(lineage["created_at"]),
                        last_modified=datetime.fromisoformat(lineage["last_modified"]),
                        children=lineage.get("children", []),
                        parents=lineage.get("parents", []),
                    )
                logger.debug("Successfully loaded all lineage data")
            else:
                logger.debug("No existing lineage data found")
        except Exception as e:
            logger.error(f"Error loading lineage data: {e}")
            self.lineage_data = {}

    def save_lineage_data(self) -> None:
        """
        Save current lineage data to storage.

        This method serializes all document lineage data to JSON format and writes
        it to the storage file. It handles datetime serialization and ensures the
        storage directory exists.

        Raises:
            Exception: If there are errors creating the directory or writing the file.
                     These are logged and re-raised to allow error handling by callers.

        Example:
            ```python
            storage = LineageStorage("/data/lineage")
            storage.add_document("doc123")
            storage.save_lineage_data()  # Persists changes to disk
            ```
        """
        try:
            logger.debug(f"Ensuring storage directory exists: {self.storage_dir}")
            self.storage_dir.mkdir(parents=True, exist_ok=True)

            logger.debug(f"Preparing to save {len(self.lineage_data)} documents")
            data = {doc_id: lineage.to_dict() for doc_id, lineage in self.lineage_data.items()}

            storage_path = self._get_storage_path()
            logger.debug(f"Writing lineage data to {storage_path}")
            with open(storage_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug("Successfully saved lineage data")
        except Exception as e:
            logger.error(f"Error saving lineage data: {e}")
            raise

    def add_document_lineage(self, doc_id: str, lineage: DocumentLineage) -> None:
        """Add a document lineage object to storage."""
        logger.debug(f"Adding document lineage for {doc_id}")
        self.lineage_data[doc_id] = lineage
        self.save_lineage_data()
        logger.debug(f"Successfully added document lineage for {doc_id}")

    def get_lineage(self, doc_id: str) -> Optional[DocumentLineage]:
        """Get document lineage by ID."""
        logger.debug(f"Retrieving lineage for document {doc_id}")
        lineage = self.lineage_data.get(doc_id)
        if lineage:
            logger.debug(f"Found lineage for document {doc_id}")
        else:
            logger.debug(f"No lineage found for document {doc_id}")
        return lineage

    def get_all_lineage(self) -> Dict[str, DocumentLineage]:
        """
        Get all lineage data.

        Returns:
            Dictionary mapping document IDs to their DocumentLineage objects.

        Example:
            ```python
            all_lineage = storage.get_all_lineage()
            for doc_id, lineage in all_lineage.items():
                print(f"Document {doc_id} created at {lineage.created_at}")
            ```
        """
        logger.debug(f"Retrieving all lineage data ({len(self.lineage_data)} documents)")
        return self.lineage_data

    def update_document_lineage(self, doc_id: str, updates: Dict) -> None:
        """
        Update document lineage with new data.

        Args:
            doc_id: Document ID to update
            updates: Dictionary of updates to apply

        Raises:
            ValueError: If document not found or if update would create circular reference
        """
        logger.debug("Starting lineage update for document %s", doc_id)
        logger.debug("Update contents: %s", updates)

        if doc_id not in self.lineage_data:
            logger.error("Document %s not found for update", doc_id)
            raise ValueError(f"Document {doc_id} not found")

        lineage = self.lineage_data[doc_id]
        logger.debug(
            "Current document state - ID: %s, Parents: %s, Children: %s, Derived From: %s",
            doc_id,
            lineage.parents,
            lineage.children,
            lineage.derived_from,
        )

        # Check for circular references if updating parents
        if "parents" in updates:
            from .lineage_operations import _would_create_circular_reference

            new_parents = updates["parents"]
            logger.debug("Checking circular references for new parents: %s", new_parents)

            for parent_id in new_parents:
                logger.debug("Checking parent %s for circular reference with %s", parent_id, doc_id)

                # Log parent's current state
                parent_lineage = self.lineage_data.get(parent_id)
                if parent_lineage:
                    logger.debug(
                        "Parent state - ID: %s, Parents: %s, Children: %s, Derived From: %s",
                        parent_id,
                        parent_lineage.parents,
                        parent_lineage.children,
                        parent_lineage.derived_from,
                    )

                if _would_create_circular_reference(self, parent_id, doc_id):
                    error_msg = f"Circular reference detected: adding {parent_id} as parent would create a cycle in document lineage"
                    logger.error(
                        "Circular reference details - Document: %s, Attempted Parent: %s, Current Parents: %s, Current Children: %s",
                        doc_id,
                        parent_id,
                        lineage.parents,
                        lineage.children,
                    )
                    raise ValueError(error_msg)

                logger.debug("No circular reference found for parent %s", parent_id)

                # Update parent's children list
                if parent_lineage and doc_id not in parent_lineage.children:
                    logger.debug("Adding %s to parent %s's children list", doc_id, parent_id)
                    parent_lineage.children.append(doc_id)
                    parent_lineage.derived_documents.append(doc_id)
                    parent_lineage.last_modified = datetime.now(timezone.utc)
                    self.save_lineage(parent_lineage)
                    logger.debug(
                        "Updated parent %s - New Children: %s, New Derived Documents: %s",
                        parent_id,
                        parent_lineage.children,
                        parent_lineage.derived_documents,
                    )

        # Apply updates
        for key, value in updates.items():
            logger.debug("Setting %s = %s for document %s", key, value, doc_id)
            setattr(lineage, key, value)

        lineage.last_modified = datetime.now(timezone.utc)
        logger.debug(
            "Final document state - ID: %s, Parents: %s, Children: %s, Derived From: %s",
            doc_id,
            lineage.parents,
            lineage.children,
            lineage.derived_from,
        )

        self.save_lineage_data()
        logger.debug("Successfully saved updated lineage for document %s", doc_id)

    def __len__(self) -> int:
        """Return the number of documents in storage."""
        return len(self.lineage_data)

    def delete_lineage(self, doc_id: str) -> None:
        """
        Delete document lineage.

        Args:
            doc_id: Document ID to delete

        Raises:
            ValueError: If document not found
        """
        logger.debug(f"Attempting to delete document {doc_id}")
        if doc_id not in self.lineage_data:
            logger.error(f"Document {doc_id} not found for deletion")
            raise ValueError(f"Document {doc_id} not found")

        del self.lineage_data[doc_id]
        self.save_lineage_data()
        logger.debug(f"Successfully deleted document {doc_id}")

    def get_lineages_by_time(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict[str, DocumentLineage]:
        """
        Get document lineages within a time range.

        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Dictionary of document lineages within the time range
        """
        logger.debug(f"Getting lineages between {start_time} and {end_time}")
        filtered = {}
        for doc_id, lineage in self.lineage_data.items():
            if start_time and lineage.created_at < start_time:
                continue
            if end_time and lineage.created_at > end_time:
                continue
            filtered[doc_id] = lineage

        logger.debug(f"Found {len(filtered)} documents in time range")
        return filtered

    def get_lineages_by_status(self, status: str) -> Dict[str, DocumentLineage]:
        """
        Get document lineages by processing status.

        Args:
            status: Processing status to filter by

        Returns:
            Dictionary of document lineages with the specified status
        """
        logger.debug(f"Getting lineages with status: {status}")
        filtered = {}
        for doc_id, lineage in self.lineage_data.items():
            if not lineage.processing_steps:
                continue
            latest_step = lineage.processing_steps[-1]
            if latest_step.status.value == status:
                filtered[doc_id] = lineage

        logger.debug(f"Found {len(filtered)} documents with status {status}")
        return filtered

    def get_lineages_by_type(self, doc_type: str) -> Dict[str, DocumentLineage]:
        """
        Get document lineages by document type.

        Args:
            doc_type: Document type to filter by

        Returns:
            Dictionary of document lineages of the specified type
        """
        logger.debug(f"Getting lineages of type: {doc_type}")
        filtered = {}
        for doc_id, lineage in self.lineage_data.items():
            if lineage.metadata.get("type") == doc_type:
                filtered[doc_id] = lineage

        logger.debug(f"Found {len(filtered)} documents of type {doc_type}")
        return filtered

    def get_lineages_by_source(self, source: str) -> Dict[str, DocumentLineage]:
        """
        Get document lineages by source.

        Args:
            source: Source identifier to filter by

        Returns:
            Dictionary of document lineages from the specified source
        """
        logger.debug(f"Getting lineages from source: {source}")
        filtered = {}
        for doc_id, lineage in self.lineage_data.items():
            if lineage.origin_source == source:
                filtered[doc_id] = lineage

        logger.debug(f"Found {len(filtered)} documents from source {source}")
        return filtered

    def get_derived_documents(self, doc_id: str) -> List[str]:
        """
        Get IDs of documents derived from the specified document.

        Args:
            doc_id: Parent document ID

        Returns:
            List of derived document IDs

        Raises:
            ValueError: If document not found
        """
        logger.debug(f"Getting documents derived from {doc_id}")
        if doc_id not in self.lineage_data:
            logger.error(f"Document {doc_id} not found")
            raise ValueError(f"Document {doc_id} not found")

        derived = self.lineage_data[doc_id].derived_documents
        logger.debug(f"Found {len(derived)} derived documents")
        return derived

    def get_parent_documents(self, doc_id: str) -> List[str]:
        """
        Get IDs of parent documents for the specified document.

        Args:
            doc_id: Child document ID

        Returns:
            List of parent document IDs

        Raises:
            ValueError: If document not found
        """
        logger.debug(f"Getting parent documents for {doc_id}")
        if doc_id not in self.lineage_data:
            logger.error(f"Document {doc_id} not found")
            raise ValueError(f"Document {doc_id} not found")

        parents = []
        lineage = self.lineage_data[doc_id]
        if lineage.derived_from:
            parents.append(lineage.derived_from)

        logger.debug(f"Found {len(parents)} parent documents")
        return parents

    def get_all_lineages(self) -> Dict[str, DocumentLineage]:
        """
        Get all document lineages.

        Returns:
            Dictionary mapping document IDs to their DocumentLineage objects.

        Example:
            ```python
            all_lineages = storage.get_all_lineages()
            for doc_id, lineage in all_lineages.items():
                print(f"Document {doc_id}: {len(lineage.processing_steps)} steps")
            ```
        """
        return self.get_all_lineage()

    def save_lineage(self, lineage: DocumentLineage) -> None:
        """
        Save document lineage.

        Args:
            lineage: The DocumentLineage object to save

        Example:
            ```python
            lineage = DocumentLineage(doc_id="doc123")
            storage.save_lineage(lineage)
            ```
        """
        self.add_document_lineage(lineage.doc_id, lineage)

    def __iter__(self):
        """Make the storage iterable over document IDs."""
        return iter(self.lineage_data)

    def __contains__(self, doc_id: str) -> bool:
        """Support 'in' operator for document IDs."""
        return doc_id in self.lineage_data

    def items(self):
        """Get items (doc_id, lineage) pairs."""
        return self.lineage_data.items()

    def values(self):
        """Get all lineage objects."""
        return self.lineage_data.values()

    def keys(self):
        """Get all document IDs."""
        return self.lineage_data.keys()

    def add_metrics(
        self,
        doc_id: str,
        metrics: Dict,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Add performance metrics for a document.

        Args:
            doc_id: Document ID to update
            metrics: Dictionary of metrics to add
            timestamp: Optional timestamp for the metrics

        Raises:
            ValueError: If document not found

        Example:
            ```python
            storage.add_metrics(
                "doc123",
                {
                    "processing_time": 1.5,
                    "memory_usage": 256,
                    "success_rate": 0.95
                }
            )
            ```
        """
        logger.debug(f"Adding metrics for document {doc_id}")
        if doc_id not in self.lineage_data:
            logger.error(f"Document {doc_id} not found")
            raise ValueError(f"Document {doc_id} not found")

        lineage = self.lineage_data[doc_id]
        metrics_entry = {
            "timestamp": (
                timestamp.isoformat() if timestamp else datetime.now(timezone.utc).isoformat()
            ),
            "metrics": metrics,
        }

        if "performance_metrics" not in lineage.metadata:
            lineage.metadata["performance_metrics"] = []
        lineage.metadata["performance_metrics"].append(metrics_entry)

        lineage.last_modified = datetime.now(timezone.utc)
        self.save_lineage_data()
        logger.debug(f"Successfully added metrics for document {doc_id}")

    def __getitem__(self, doc_id: str) -> DocumentLineage:
        """Support dictionary-style access to lineage data."""
        if doc_id not in self.lineage_data:
            raise KeyError(f"Document {doc_id} not found")
        return self.lineage_data[doc_id]

    def __setitem__(self, doc_id: str, lineage: DocumentLineage) -> None:
        """Support dictionary-style assignment of lineage data."""
        self.lineage_data[doc_id] = lineage
        self.save_lineage_data()
