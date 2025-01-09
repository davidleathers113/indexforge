"""
Manages document transformations and their recording.

This module provides functionality for recording and managing document transformations,
including tracking transformation history and metadata.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from .enums import TransformationType
from .models import DocumentLineage, Transformation

logger = logging.getLogger(__name__)


def record_transformation(
    storage: Any,
    doc_id: str,
    transform_type: Union[TransformationType, str],
    description: str = "",
    parameters: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
) -> None:
    """Record a transformation applied to a document."""
    logger.debug(
        "Recording transformation - Doc: %s, Type: %s, Description: %s",
        doc_id,
        transform_type,
        description,
    )
    logger.debug("Parameters: %s", parameters)
    logger.debug("Metadata: %s", metadata)

    lineage = storage.get_lineage(doc_id)
    if not lineage:
        logger.error("Document %s not found", doc_id)
        raise ValueError(f"Document {doc_id} not found")
    logger.debug("Found document lineage: %s", lineage)

    if isinstance(transform_type, str):
        logger.debug("Converting transform_type from string '%s' to enum", transform_type)
        try:
            transform_type = TransformationType(transform_type)
        except ValueError as e:
            logger.error("Invalid transform type '%s': %s", transform_type, e)
            raise

    transformation = Transformation(
        transform_type=transform_type,
        description=description,
        parameters=parameters or {},
        metadata=metadata or {},
    )
    logger.debug("Created transformation: %s", transformation)

    lineage.transformations.append(transformation)
    lineage.last_modified = datetime.now(timezone.utc)
    storage.save_lineage(lineage)
    logger.debug(
        "Successfully recorded transformation. Total transformations: %d",
        len(lineage.transformations),
    )


def get_transformation_history(
    lineage: DocumentLineage,
    transform_type: Optional[Union[TransformationType, str]] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> list[Transformation]:
    """Get transformation history for a document with optional filters."""
    logger.debug(
        "Getting transformation history - Type: %s, Start: %s, End: %s",
        transform_type,
        start_time,
        end_time,
    )
    logger.debug("Initial lineage state: %s", lineage)

    if isinstance(transform_type, str):
        logger.debug("Converting transform_type from string '%s' to enum", transform_type)
        try:
            transform_type = TransformationType(transform_type)
        except ValueError as e:
            logger.error("Invalid transform type '%s': %s", transform_type, e)
            raise

    transformations = lineage.transformations
    logger.debug("Found %d total transformations", len(transformations))

    if transform_type:
        transformations = [t for t in transformations if t.transform_type == transform_type]
        logger.debug(
            "Filtered to %d transformations by type %s",
            len(transformations),
            transform_type,
        )

    if start_time:
        transformations = [t for t in transformations if t.timestamp >= start_time]
        logger.debug(
            "Filtered to %d transformations after %s",
            len(transformations),
            start_time,
        )

    if end_time:
        transformations = [t for t in transformations if t.timestamp <= end_time]
        logger.debug(
            "Filtered to %d transformations before %s",
            len(transformations),
            end_time,
        )

    logger.debug("Returning %d transformations", len(transformations))
    return transformations
