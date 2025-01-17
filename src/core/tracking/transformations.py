"""Document transformation management and tracking.

This module provides functionality for managing and recording document transformations,
including tracking transformation history, metadata, and relationships between
transformed documents.

Key Features:
    - Transformation recording
    - History tracking
    - Metadata management
    - Relationship tracking
    - Validation
    - Error handling

Example:
    ```python
    from datetime import datetime, timedelta
    from src.core.tracking.transformations import TransformationManager
    from src.core.models.lineage import DocumentLineage
    from src.core.storage.tracking import LineageStorage

    # Initialize components
    storage = LineageStorage("/path/to/storage")
    manager = TransformationManager(storage)

    # Record a transformation
    manager.record_transformation(
        doc_id="doc123",
        transform_type="TEXT_EXTRACTION",
        description="Extract text from PDF",
        parameters={"format": "pdf"},
    )

    # Get transformation history
    history = manager.get_transformation_history(
        doc_id="doc123",
        transform_type="TEXT_EXTRACTION",
        start_time=datetime.now() - timedelta(days=1),
    )
    ```
"""

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from src.core.storage.tracking import LineageStorage

logger = logging.getLogger(__name__)


class TransformationType(str, Enum):
    """Types of document transformations."""

    TEXT_EXTRACTION = "TEXT_EXTRACTION"
    IMAGE_PROCESSING = "IMAGE_PROCESSING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    METADATA_EXTRACTION = "METADATA_EXTRACTION"
    FORMAT_CONVERSION = "FORMAT_CONVERSION"
    SUMMARIZATION = "SUMMARIZATION"
    TRANSLATION = "TRANSLATION"
    OCR = "OCR"
    ANONYMIZATION = "ANONYMIZATION"


class TransformationError(Exception):
    """Base exception for transformation errors."""


class DocumentNotFoundError(TransformationError):
    """Document not found in storage."""


class InvalidTransformationError(TransformationError):
    """Invalid transformation type or parameters."""


class TransformationManager:
    """Manager for document transformations."""

    def __init__(self, storage: LineageStorage):
        """Initialize transformation manager.

        Args:
            storage: LineageStorage instance for persistence.
        """
        self.storage = storage

    def record_transformation(
        self,
        doc_id: str,
        transform_type: Union[TransformationType, str],
        description: str = "",
        parameters: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Record a transformation applied to a document.

        Args:
            doc_id: Document ID.
            transform_type: Type of transformation.
            description: Optional description of the transformation.
            parameters: Optional parameters used in the transformation.
            metadata: Optional metadata about the transformation.

        Raises:
            DocumentNotFoundError: If document not found.
            InvalidTransformationError: If transform_type is invalid.
        """
        logger.debug(
            "Recording transformation - Doc: %s, Type: %s, Description: %s",
            doc_id,
            transform_type,
            description,
        )
        logger.debug("Parameters: %s", parameters)
        logger.debug("Metadata: %s", metadata)

        # Get document lineage
        lineage = self.storage.get_lineage(doc_id)
        if not lineage:
            logger.error("Document %s not found", doc_id)
            raise DocumentNotFoundError(f"Document {doc_id} not found")

        # Validate and convert transform type
        if isinstance(transform_type, str):
            try:
                transform_type = TransformationType(transform_type.upper())
            except ValueError as e:
                logger.error("Invalid transform type '%s': %s", transform_type, e)
                raise InvalidTransformationError(f"Invalid transform type: {transform_type}") from e

        # Create transformation record
        transformation = {
            "type": transform_type,
            "timestamp": datetime.now(UTC),
            "description": description,
            "parameters": parameters or {},
            "metadata": metadata or {},
        }

        # Update lineage
        lineage.transformations.append(transformation)
        self.storage.save_lineage(lineage)

        logger.info(
            "Recorded transformation %s for document %s",
            transform_type,
            doc_id,
        )

    def get_transformation_history(
        self,
        doc_id: str,
        transform_type: Optional[Union[TransformationType, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict]:
        """Get transformation history for a document.

        Args:
            doc_id: Document ID.
            transform_type: Optional type to filter by.
            start_time: Optional start of time range.
            end_time: Optional end of time range.

        Returns:
            List of transformation records.

        Raises:
            DocumentNotFoundError: If document not found.
            InvalidTransformationError: If transform_type is invalid.
        """
        # Get document lineage
        lineage = self.storage.get_lineage(doc_id)
        if not lineage:
            logger.error("Document %s not found", doc_id)
            raise DocumentNotFoundError(f"Document {doc_id} not found")

        # Convert transform type if string
        if isinstance(transform_type, str):
            try:
                transform_type = TransformationType(transform_type.upper())
            except ValueError as e:
                logger.error("Invalid transform type '%s': %s", transform_type, e)
                raise InvalidTransformationError(f"Invalid transform type: {transform_type}") from e

        # Filter transformations
        transformations = lineage.transformations
        if transform_type:
            transformations = [t for t in transformations if t["type"] == transform_type]
        if start_time:
            transformations = [t for t in transformations if t["timestamp"] >= start_time]
        if end_time:
            transformations = [t for t in transformations if t["timestamp"] <= end_time]

        return transformations

    def get_documents_by_transformation(
        self,
        transform_type: Union[TransformationType, str],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, List[Dict]]:
        """Get all documents that have undergone a specific transformation.

        Args:
            transform_type: Type of transformation to search for.
            start_time: Optional start of time range.
            end_time: Optional end of time range.

        Returns:
            Dictionary mapping document IDs to their transformation records.

        Raises:
            InvalidTransformationError: If transform_type is invalid.
        """
        # Validate transform type
        if isinstance(transform_type, str):
            try:
                transform_type = TransformationType(transform_type.upper())
            except ValueError as e:
                logger.error("Invalid transform type '%s': %s", transform_type, e)
                raise InvalidTransformationError(f"Invalid transform type: {transform_type}") from e

        results = {}
        for doc_id, lineage in self.storage.items():
            transformations = self.get_transformation_history(
                doc_id, transform_type, start_time, end_time
            )
            if transformations:
                results[doc_id] = transformations

        return results

    def get_latest_transformation(
        self,
        doc_id: str,
        transform_type: Optional[Union[TransformationType, str]] = None,
    ) -> Optional[Dict]:
        """Get the most recent transformation for a document.

        Args:
            doc_id: Document ID.
            transform_type: Optional type to filter by.

        Returns:
            Most recent transformation record or None.

        Raises:
            DocumentNotFoundError: If document not found.
            InvalidTransformationError: If transform_type is invalid.
        """
        transformations = self.get_transformation_history(doc_id, transform_type)
        if not transformations:
            return None
        return max(transformations, key=lambda x: x["timestamp"])
