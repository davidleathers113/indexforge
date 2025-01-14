"""
Document lineage tracking and management system.

This module provides a high-level interface for tracking document transformations,
processing steps, and relationships within a document processing pipeline. It serves
as the main entry point for document lineage operations, delegating specific
functionality to specialized components.

Key Features:
    - Document lifecycle tracking
    - Processing step management
    - Error and warning logging
    - Performance metrics collection
    - Health monitoring
    - Storage management

Example:
    ```python
    # Initialize the lineage manager
    manager = DocumentLineageManager("/path/to/storage")

    # Add a new document
    manager.add_document(
        doc_id="doc123",
        origin_id="source456",
        metadata={"type": "pdf", "pages": 10}
    )

    # Record processing steps
    manager.add_processing_step(
        doc_id="doc123",
        step_name="text_extraction",
        status="success",
        details={"extracted_chars": 5000}
    )

    # Get document lineage
    lineage = manager.get_lineage("doc123")
    ```
"""

import logging
from datetime import datetime
from typing import Optional, Union

from .enums import TransformationType
from .models import Transformation
from .storage import LineageStorage

logger = logging.getLogger(__name__)


def _get_transformation_history(
    lineage: dict,
    transform_type: Optional[Union[TransformationType, str]] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> list[Transformation]:
    """Get transformation history for a document with optional filters."""
    logger.debug(
        f"Getting transformation history with filters - type: {transform_type}, start: {start_time}, end: {end_time}"
    )
    transformations = lineage.get("transformations", [])
    logger.debug(f"Found {len(transformations)} total transformations")

    if transform_type:
        transformations = [t for t in transformations if t["type"] == transform_type]
        logger.debug(f"Filtered to {len(transformations)} transformations by type")
    if start_time:
        transformations = [t for t in transformations if t["timestamp"] >= start_time]
        logger.debug(f"Filtered to {len(transformations)} transformations by start time")
    if end_time:
        transformations = [t for t in transformations if t["timestamp"] <= end_time]
        logger.debug(f"Filtered to {len(transformations)} transformations by end time")

    return [Transformation(**t) for t in transformations]


class DocumentLineageManager:
    """
    High-level manager for document lineage tracking and operations.

    This class serves as the main interface for tracking document transformations,
    processing steps, and relationships. It delegates specific operations to
    specialized components while maintaining a consistent interface for clients.

    Attributes:
        storage (LineageStorage): Storage manager for persisting lineage data.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize the document lineage manager."""
        logger.debug(f"Initializing DocumentLineageManager with storage dir: {storage_dir}")
        self.storage = LineageStorage(storage_dir)

    def get_transformation_history(
        self,
        doc_id: str,
        transform_type: Optional[Union[TransformationType, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[Transformation]:
        """Get transformation history for a document with optional filters."""
        logger.debug(f"Getting transformation history for document {doc_id}")
        lineage = self.storage.get_lineage(doc_id)
        if not lineage:
            logger.error(f"Document {doc_id} not found in lineage tracking")
            raise ValueError(f"Document {doc_id} not found in lineage tracking")
        return _get_transformation_history(lineage, transform_type, start_time, end_time)
