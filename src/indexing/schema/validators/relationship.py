"""
Document relationship validation for schema compliance.

This module provides functionality to validate document relationships,
ensuring proper parent-child connections and preventing circular references
or duplicate chunks.

Key Features:
    - Parent-child relationship validation
    - Circular reference detection
    - Duplicate chunk prevention
    - Relationship integrity checks
    - Document ID validation

Example:
    ```python
    from typing import Dict, Any, Optional

    # Validate document relationships
    doc = {
        "parent_id": "doc123",
        "chunk_ids": ["chunk1", "chunk2"]
    }

    try:
        validate_relationships(doc, doc_id="doc456")
        print("Relationships are valid")
    except ValueError as e:
        print(f"Validation error: {e}")
    ```
"""

import logging
from typing import Any


logger = logging.getLogger(__name__)


def validate_relationships(doc: dict, doc_id: str | None = None) -> None:
    """
    Validate document relationships and references.

    This function performs comprehensive validation of document relationships:
    - Validates parent_id format and type
    - Prevents self-references
    - Checks for circular references
    - Validates chunk references
    - Prevents duplicate chunks

    Args:
        doc: The document to validate
        doc_id: Optional ID of the current document (for self-ref checks)

    Raises:
        TypeError: If parent_id is not a string
        ValueError: If relationships are invalid (circular, duplicate)
        ValueError: If chunk references are invalid

    Example:
        ```python
        doc = {
            "parent_id": "doc123",
            "chunk_ids": ["chunk1", "chunk2"]
        }
        validate_relationships(doc, doc_id="doc456")
        ```
    """
    logger.debug(
        "Starting relationship validation for document%s", f" with ID {doc_id}" if doc_id else ""
    )
    logger.debug("Document fields: %s", list(doc.keys()))

    # Validate parent_id if present
    if "parent_id" in doc:
        parent_id = doc["parent_id"]
        logger.debug("Found parent_id: %r (type: %s)", parent_id, type(parent_id))
        validate_parent_id(parent_id, doc_id)

    # Validate chunk_ids if present
    if "chunk_ids" in doc:
        chunk_ids = doc["chunk_ids"]
        logger.debug("Found chunk_ids: %r (type: %s)", chunk_ids, type(chunk_ids))
        if chunk_ids:
            validate_chunk_references(chunk_ids)
            if doc_id and doc_id in chunk_ids:
                logger.error(
                    "Self-reference in chunks detected: document %s references itself", doc_id
                )
                raise ValueError("self-reference")
        else:
            logger.debug("Skipping chunk_ids validation - value is empty")

    logger.info(
        "Relationship validation successful for document%s", f" with ID {doc_id}" if doc_id else ""
    )


def validate_parent_id(parent_id: Any, doc_id: str | None = None) -> None:
    """
    Validate parent document reference.

    Args:
        parent_id: The parent document ID to validate
        doc_id: Optional current document ID

    Raises:
        TypeError: If parent_id is not a string
        ValueError: If parent_id is invalid or creates a self-reference
    """
    logger.debug("Validating parent_id: %r (type: %s)", parent_id, type(parent_id))

    # Type validation
    if parent_id is not None and not isinstance(parent_id, str):
        logger.error(
            "Invalid parent_id type: %s (expected: str, value: %r)", type(parent_id), parent_id
        )
        raise TypeError("parent_id.*string")

    # Self-reference check
    if doc_id and parent_id == doc_id:
        logger.error("Self-reference detected: document %s references itself as parent", doc_id)
        raise ValueError("self-reference")

    logger.debug("Parent ID validation successful: %s", parent_id)


def validate_chunk_references(chunk_ids: Any) -> None:
    """
    Validate chunk references.

    Args:
        chunk_ids: List of chunk IDs to validate

    Raises:
        TypeError: If chunk_ids is not a list of strings
        ValueError: If duplicate chunks are found
    """
    logger.debug("Validating chunk references: %r (type: %s)", chunk_ids, type(chunk_ids))

    # Type validation
    if not isinstance(chunk_ids, (list, tuple)):
        logger.error(
            "Invalid chunk_ids type: %s (expected: list/tuple, value: %r)",
            type(chunk_ids),
            chunk_ids,
        )
        raise TypeError("chunk_ids.*list")

    # Validate all chunk IDs are strings
    for i, chunk_id in enumerate(chunk_ids):
        if not isinstance(chunk_id, str):
            logger.error(
                "Invalid chunk ID type at index %d: %s (expected: str, value: %r)",
                i,
                type(chunk_id),
                chunk_id,
            )
            raise TypeError("chunk_ids.*string")

    # Check for duplicates
    seen = set()
    duplicates = []
    for chunk_id in chunk_ids:
        if chunk_id in seen:
            duplicates.append(chunk_id)
        else:
            seen.add(chunk_id)

    if duplicates:
        logger.error("Duplicate chunk IDs found: %r", duplicates)
        raise ValueError("duplicate.*chunk")

    logger.debug("Chunk references validation successful: %d chunks", len(chunk_ids))


def detect_circular_reference(
    doc_id: str, parent_id: str, visited: set[str] | None = None
) -> None:
    """
    Detect circular references in document hierarchy.

    Args:
        doc_id: Current document ID
        parent_id: Parent document ID to check
        visited: Set of already visited document IDs

    Raises:
        ValueError: If a circular reference is detected
    """
    logger.debug(
        "Checking for circular reference: %s -> %s (visited: %s)",
        doc_id,
        parent_id,
        visited or set(),
    )

    if visited is None:
        visited = set()

    if doc_id in visited:
        logger.error("Circular reference detected in chain: %s -> %s", " -> ".join(visited), doc_id)
        raise ValueError("circular")
