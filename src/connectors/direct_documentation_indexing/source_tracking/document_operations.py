"""
Basic document operations for the source tracking system.

This module provides core document management functionality like adding new documents
and managing their basic metadata.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .lineage_operations import _would_create_circular_reference
from .models import DocumentLineage

logger = logging.getLogger(__name__)


def add_document(
    storage,
    doc_id: str,
    parent_ids: Optional[List[str]] = None,
    origin_id: Optional[str] = None,
    origin_source: Optional[str] = None,
    origin_type: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> None:
    """Add a new document to lineage tracking.

    Args:
        storage: LineageStorage instance
        doc_id: ID of the document to add
        parent_ids: Optional list of parent document IDs
        origin_id: Optional ID from the source system
        origin_source: Optional source system identifier
        origin_type: Optional document type from source
        metadata: Optional metadata about the document

    Raises:
        ValueError: If document already exists or parent not found
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
        # Check for circular references first
        if parent_ids:
            logger.debug("Processing parent relationships for %d parents", len(parent_ids))
            for parent_id in parent_ids:
                logger.debug("Processing parent: %s", parent_id)

                # Get parent document
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
                if _would_create_circular_reference(storage, parent_id, doc_id):
                    logger.error(
                        "Circular reference detected - Parent: %s, Child: %s would create a cycle",
                        parent_id,
                        doc_id,
                    )
                    raise ValueError(
                        f"Circular reference detected: adding {doc_id} as child of {parent_id} would create a cycle"
                    )
                logger.debug("No circular references found with parent %s", parent_id)

        # Check if document already exists
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
        lineage = DocumentLineage(
            doc_id=doc_id,
            origin_id=origin_id,
            origin_source=origin_source,
            origin_type=origin_type,
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc),
        )
        logger.debug("Created lineage object: %s", lineage)

        # Add parent relationships if specified
        if parent_ids:
            for parent_id in parent_ids:
                # Update parent's children list
                parent = storage.get_lineage(parent_id)
                if doc_id not in parent.children:
                    logger.debug("Adding %s to parent %s's children list", doc_id, parent_id)
                    parent.children.append(doc_id)
                    parent.derived_documents.append(doc_id)
                    parent.last_modified = datetime.now(timezone.utc)
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
                    lineage.derived_from = parent_id  # Set first parent as direct parent
                    logger.debug(
                        "Updated child %s - Parents: %s, Derived from: %s",
                        doc_id,
                        lineage.parents,
                        lineage.derived_from,
                    )

        # Save the new document
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
