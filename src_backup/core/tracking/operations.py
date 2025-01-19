"""
Document operations for the core tracking system.

This module provides core document management functionality including:
- Adding new documents with lineage tracking
- Managing document relationships
- Handling document metadata
"""

from datetime import UTC, datetime
import logging
from typing import Any

from src.core.interfaces.storage import LineageStorage
from src.core.models.lineage import DocumentLineage
from src.core.tracking.validation.strategies.circular import validate_no_circular_reference


logger = logging.getLogger(__name__)


def add_document(
    storage: LineageStorage,
    doc_id: str,
    parent_ids: list[str] | None = None,
    origin_id: str | None = None,
    origin_source: str | None = None,
    origin_type: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Add a new document to lineage tracking.

    This function creates a new document entry in the lineage tracking system,
    establishing parent-child relationships if specified and managing metadata.

    Args:
        storage: LineageStorage instance for persistence
        doc_id: Unique identifier for the document
        parent_ids: Optional list of parent document IDs to establish lineage
        origin_id: Optional identifier from the source system
        origin_source: Optional identifier for the source system
        origin_type: Optional document type classification
        metadata: Optional dictionary of additional document metadata

    Raises:
        ValueError: If document already exists, parent not found, or would create circular reference
    """
    logger.info("Adding new document to lineage tracking - ID: %s", doc_id)
    logger.debug(
        "Document details - Parents: %s, Origin ID: %s, Source: %s, Type: %s",
        parent_ids,
        origin_id,
        origin_source,
        origin_type,
    )
    logger.debug("Metadata: %s", metadata)

    try:
        # Validate parent relationships
        if parent_ids:
            logger.debug("Processing parent relationships for %d parents", len(parent_ids))
            for parent_id in parent_ids:
                logger.debug("Processing parent: %s", parent_id)

                # Verify parent exists
                parent = storage.get_lineage(parent_id)
                if not parent:
                    logger.error(
                        "Parent document not found - Parent: %s, Child: %s",
                        parent_id,
                        doc_id,
                    )
                    raise ValueError(f"Parent document {parent_id} not found")
                logger.debug("Found parent document: %s", parent)

                # Check for circular references
                logger.debug("Checking for circular references with parent %s", parent_id)
                if validate_no_circular_reference(storage, parent_id, doc_id):
                    logger.error(
                        "Circular reference detected - Parent: %s, Child: %s would create a cycle",
                        parent_id,
                        doc_id,
                    )
                    raise ValueError(
                        f"Circular reference detected: adding {doc_id} as child of {parent_id} would create a cycle"
                    )
                logger.debug("No circular references found with parent %s", parent_id)

        # Prevent duplicate documents
        existing_doc = storage.get_lineage(doc_id)
        if existing_doc:
            logger.error(
                "Document %s already exists in lineage tracking - Cannot add with new parents: %s",
                doc_id,
                parent_ids,
            )
            raise ValueError(f"Document {doc_id} already exists in lineage tracking")

        # Create new document lineage
        logger.debug("Creating new document lineage object")
        current_time = datetime.now(UTC)
        lineage = DocumentLineage(
            doc_id=doc_id,
            origin_id=origin_id,
            origin_source=origin_source,
            origin_type=origin_type,
            metadata=metadata or {},
            created_at=current_time,
            last_modified=current_time,
        )
        logger.debug("Created lineage object: %s", lineage)

        # Establish parent-child relationships
        if parent_ids:
            for parent_id in parent_ids:
                # Update parent's children list
                parent = storage.get_lineage(parent_id)
                if doc_id not in parent.children:
                    logger.debug("Adding %s to parent %s's children list", doc_id, parent_id)
                    parent.children.append(doc_id)
                    parent.derived_documents.append(doc_id)
                    parent.last_modified = current_time
                    storage.save_lineage(parent)
                    logger.debug(
                        "Updated parent %s - Children: %s, Derived: %s",
                        parent_id,
                        parent.children,
                        parent.derived_documents,
                    )

                # Update child's parents list
                if parent_id not in lineage.parents:
                    logger.debug("Adding %s to child %s's parents list", parent_id, doc_id)
                    lineage.parents.append(parent_id)
                    if not lineage.derived_from:  # Set first parent as direct parent
                        lineage.derived_from = parent_id
                    logger.debug(
                        "Updated child %s - Parents: %s, Derived from: %s",
                        doc_id,
                        lineage.parents,
                        lineage.derived_from,
                    )

        # Persist the new document
        logger.debug("Saving new document lineage to storage")
        storage.save_lineage(lineage)
        logger.info(
            "Successfully added document %s with %d parents",
            doc_id,
            len(parent_ids) if parent_ids else 0,
        )

    except Exception as e:
        logger.error(
            "Failed to add document %s: %s",
            doc_id,
            str(e),
            exc_info=True,
        )
        raise
