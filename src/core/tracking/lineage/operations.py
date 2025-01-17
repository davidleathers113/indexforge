"""
Manages document lineage operations and relationships.

This module provides functionality for managing relationships between documents,
including derivation chains and parent-child relationships.
"""

import logging
from datetime import UTC, datetime
from typing import Dict, List, Optional, Union

from src.core.interfaces.storage import LineageStorage
from src.core.tracking.models.lineage import DocumentLineage
from src.core.tracking.models.transformation import TransformationType
from src.core.tracking.validation.strategies.circular import validate_no_circular_reference

logger = logging.getLogger(__name__)


def add_derivation(
    storage: LineageStorage,
    parent_id: str,
    derived_id: str,
    transform_type: Optional[Union[TransformationType, str]] = None,
    description: str = "",
    parameters: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
) -> None:
    """Link a derived document to its parent.

    Args:
        storage: LineageStorage instance
        parent_id: ID of the parent document
        derived_id: ID of the derived document
        transform_type: Type of transformation applied
        description: Description of the derivation
        parameters: Parameters used in the transformation
        metadata: Additional metadata about the derivation

    Raises:
        ValueError: If parent or derived document not found, or if circular reference detected
    """
    logger.info(
        "Adding derivation relationship - Parent: %s, Derived: %s",
        parent_id,
        derived_id,
    )
    logger.debug("Transform type: %s, Description: %s", transform_type, description)
    logger.debug("Parameters: %s", parameters)
    logger.debug("Metadata: %s", metadata)

    # Validate input parameters
    if not parent_id or not derived_id:
        logger.error("Invalid document IDs - Parent: %s, Derived: %s", parent_id, derived_id)
        raise ValueError("Parent and derived document IDs must be provided")

    # Check for self-referential derivation
    if parent_id == derived_id:
        logger.error("Attempted to create self-referential derivation for document %s", parent_id)
        raise ValueError("Document cannot be derived from itself")

    try:
        # Get parent lineage
        parent_lineage = storage.get_lineage(parent_id)
        if not parent_lineage:
            logger.error("Parent document %s not found in lineage tracking", parent_id)
            raise ValueError(f"Parent document {parent_id} not found")
        logger.debug("Parent lineage found: %s", parent_lineage)

        # Get derived lineage
        derived_lineage = storage.get_lineage(derived_id)
        if not derived_lineage:
            logger.error("Derived document %s not found in lineage tracking", derived_id)
            raise ValueError(f"Derived document {derived_id} not found")
        logger.debug("Derived lineage found: %s", derived_lineage)

        # Check for circular references
        if validate_no_circular_reference(storage, parent_id, derived_id):
            logger.error(
                "Circular reference detected: %s -> %s would create a cycle",
                parent_id,
                derived_id,
            )
            raise ValueError(
                f"Circular reference detected: adding {derived_id} as parent of {parent_id} would create a cycle"
            )

        # Update parent document
        if derived_id not in parent_lineage.derived_documents:
            logger.debug("Adding %s to parent's derived documents", derived_id)
            parent_lineage.derived_documents.append(derived_id)
            parent_lineage.children.append(derived_id)
            parent_lineage.last_modified = datetime.now(UTC)
            storage.save_lineage(parent_lineage)
            logger.debug(
                "Updated parent lineage - Derived docs: %s, Children: %s",
                parent_lineage.derived_documents,
                parent_lineage.children,
            )

        # Update derived document
        if parent_id not in derived_lineage.parents:
            logger.debug("Adding %s to derived document's parents", parent_id)
            derived_lineage.parents.append(parent_id)
            derived_lineage.derived_from = parent_id  # Set the direct parent
            derived_lineage.last_modified = datetime.now(UTC)
            storage.save_lineage(derived_lineage)
            logger.debug("Updated derived lineage - Parents: %s", derived_lineage.parents)

        logger.info("Successfully added derivation relationship %s -> %s", parent_id, derived_id)

    except Exception as e:
        logger.error("Failed to add derivation relationship: %s", str(e))
        raise


def get_derivation_chain(
    storage: LineageStorage,
    doc_id: str,
    max_depth: Optional[int] = None,
) -> List[DocumentLineage]:
    """Get the chain of document derivations leading to the given document.

    Args:
        storage: LineageStorage instance
        doc_id: ID of the document to get derivation chain for
        max_depth: Maximum depth to traverse in the chain

    Returns:
        List of DocumentLineage objects representing the derivation chain from newest to oldest

    Raises:
        ValueError: If document not found or max_depth is invalid
    """
    logger.info("Getting derivation chain for document %s (max depth: %s)", doc_id, max_depth)

    if max_depth is not None and max_depth < 1:
        logger.error("Invalid max_depth value: %s", max_depth)
        raise ValueError("max_depth must be None or a positive integer")

    chain: List[DocumentLineage] = []
    current_id = doc_id
    current_depth = 0

    while current_id and (max_depth is None or current_depth < max_depth):
        lineage = storage.get_lineage(current_id)
        if not lineage:
            if not chain:  # First iteration - original document not found
                logger.error("Document %s not found in lineage tracking", doc_id)
                raise ValueError(f"Document {doc_id} not found")
            break

        chain.append(lineage)
        current_id = lineage.derived_from
        current_depth += 1
        logger.debug(
            "Added document %s to chain (depth: %s, derived from: %s)",
            lineage.doc_id,
            current_depth,
            current_id,
        )

    logger.info("Found derivation chain of length %s for document %s", len(chain), doc_id)
    return chain


def validate_lineage_relationships(lineages: List[DocumentLineage]) -> List[str]:
    """Validate relationships between documents in lineage tracking.

    Args:
        lineages: List of DocumentLineage objects to validate

    Returns:
        List of error messages, empty if no errors found
    """
    logger.info("Validating lineage relationships for %s documents", len(lineages))
    errors: List[str] = []
    doc_map = {lineage.doc_id: lineage for lineage in lineages}

    for lineage in lineages:
        # Check parent references
        for parent_id in lineage.parents:
            if parent_id not in doc_map:
                error = f"Document {lineage.doc_id} references missing parent {parent_id}"
                logger.error(error)
                errors.append(error)
            else:
                parent = doc_map[parent_id]
                if lineage.doc_id not in parent.children:
                    error = f"Parent {parent_id} missing child reference to {lineage.doc_id}"
                    logger.error(error)
                    errors.append(error)

        # Check child references
        for child_id in lineage.children:
            if child_id not in doc_map:
                error = f"Document {lineage.doc_id} references missing child {child_id}"
                logger.error(error)
                errors.append(error)
            else:
                child = doc_map[child_id]
                if lineage.doc_id not in child.parents:
                    error = f"Child {child_id} missing parent reference to {lineage.doc_id}"
                    logger.error(error)
                    errors.append(error)

    logger.info("Validation complete - Found %s errors", len(errors))
    return errors
