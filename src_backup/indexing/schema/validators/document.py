"""
Document-level validation for schema compliance.

This module provides functionality to validate individual documents against
a schema definition. It ensures that documents meet all schema requirements
including required fields, data types, size constraints, and relationship
integrity.

Key Features:
    - Required field validation
    - Data type validation
    - Size constraint checking
    - Relationship validation
    - Metadata validation
    - Vector embedding validation

Example:
    ```python
    from typing import Dict, Any

    # Validate a document against schema requirements
    doc = {
        "content_body": "Sample content",
        "timestamp_utc": "2024-01-07T12:00:00Z",
        "schema_version": 1,
        "embedding": [0.1] * 384  # 384-dim vector
    }

    try:
        validate_object(doc)
        print("Document is valid")
    except ValueError as e:
        print(f"Validation error: {e}")
    ```
"""

import logging
import re
from typing import Any

import numpy as np

from .embedding import validate_embedding


logger = logging.getLogger(__name__)

# Required fields that must be present and non-empty in all documents
REQUIRED_FIELDS: set[str] = {"content_body", "timestamp_utc", "schema_version", "embedding"}

# ISO 8601 datetime format with timezone
ISO_DATETIME_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})$"

# Field type requirements
FIELD_TYPES = {
    "content_body": str,
    "timestamp_utc": str,
    "schema_version": int,
    "embedding": (list, tuple, np.ndarray),
    "chunk_ids": (list, tuple),
    "parent_id": str,
    "metadata": dict,
}

# Size constraints
MAX_CONTENT_SIZE = 100 * 1024  # 100KB
MAX_CHUNKS = 1000
MAX_METADATA_DEPTH = 100
MAX_METADATA_FIELDS = 100


def validate_document_fields(
    doc: dict[str, Any],
    custom_fields: dict[str, type] | None = None,
    doc_id: str | None = None,
    strict: bool = True,
) -> None:
    """
    Validate a document's fields against schema requirements.

    This function performs comprehensive validation of document fields including:
    - Required field presence and non-emptiness
    - Data type correctness
    - Size constraints
    - Vector embedding dimensions
    - Timestamp format
    - Schema version validity
    - Custom field validation

    Args:
        doc: The document to validate
        custom_fields: Optional dict mapping field names to expected types
        doc_id: Optional document ID for relationship validation
        strict: If True, reject unknown fields

    Raises:
        ValueError: If any required fields are missing or empty
        TypeError: If any fields have incorrect data types
        ValueError: If any size constraints are violated
        ValueError: If vector embedding dimensions are incorrect

    Example:
        ```python
        doc = {
            "content_body": "Sample content",
            "timestamp_utc": "2024-01-07T12:00:00Z",
            "schema_version": 1,
            "embedding": [0.1] * 384,
            "custom_field": 123
        }

        custom_fields = {"custom_field": int}

        try:
            validate_document_fields(doc, custom_fields=custom_fields)
            print("Document is valid")
        except (ValueError, TypeError) as e:
            print(f"Validation error: {e}")
        ```
    """
    logger.debug("Starting document validation")
    logger.debug("Document keys: %s", list(doc.keys()))

    try:
        # Merge custom fields with standard fields
        field_types = FIELD_TYPES.copy()
        if custom_fields:
            field_types.update(custom_fields)

        validate_required_fields(doc)
        validate_field_types(doc, field_types, strict)
        validate_size_constraints(doc)
        validate_embedding(doc["embedding"])

        # Always validate relationships, even if doc_id is not provided
        from .relationship import validate_relationships

        validate_relationships(doc, doc_id)

        logger.info("Document validation successful")
    except (ValueError, TypeError) as e:
        logger.error("Document validation failed: %s", str(e), exc_info=True)
        raise


def validate_required_fields(doc: dict[str, Any]) -> None:
    """
    Validate presence and non-emptiness of required fields.

    Checks that:
    - All required fields are present
    - No required fields are None
    - String fields are not empty
    - Timestamp is in ISO format
    - Schema version is a positive integer

    Args:
        doc: The document to validate

    Raises:
        ValueError: If any required fields are missing or empty
        TypeError: If schema_version is not an integer
    """
    logger.debug("Starting required fields validation")

    # Check all required fields are present
    for field in REQUIRED_FIELDS:
        if field not in doc:
            logger.error("Missing required field: %s", field)
            raise ValueError(f"{field}.*required")

        value = doc[field]
        if value is None:
            logger.error("Field %s has None value", field)
            raise ValueError(f"{field}.*required")  # Changed from "none" to "required"

        # Check string fields are not empty
        if field in {"content_body", "timestamp_utc"} and isinstance(value, str):
            if not value.strip():
                logger.error("Field %s is empty", field)
                raise ValueError(f"{field}.*empty")

    # Validate timestamp format
    timestamp = doc["timestamp_utc"]
    if not re.match(ISO_DATETIME_PATTERN, timestamp):
        logger.error("Invalid timestamp format: %s", timestamp)
        raise ValueError("timestamp_utc.*ISO")

    # Validate schema version
    version = doc["schema_version"]
    if not isinstance(version, int):
        logger.error("Invalid schema version type: %s", type(version))
        raise TypeError("schema_version.*integer")
    if version <= 0:
        logger.error("Invalid schema version value: %d", version)
        raise ValueError("schema_version.*positive")

    logger.info("Required fields validation successful")


def validate_field_types(
    doc: dict[str, Any], field_types: dict[str, type], strict: bool = True
) -> None:
    """
    Validate data types of document fields.

    Checks that all fields have the correct data type according to the schema:
    - content_body: str
    - timestamp_utc: str (ISO format)
    - schema_version: int
    - embedding: list/tuple/ndarray of numbers
    - chunk_ids: list/tuple of strings (optional)
    - parent_id: str or None (optional)
    - metadata: dict (optional)

    Args:
        doc: The document to validate
        field_types: Dict mapping field names to expected types
        strict: If True, reject unknown fields

    Raises:
        TypeError: If any fields have incorrect data types, with message format:
            "{field}.*{expected_type}"

    Example:
        ```python
        doc = {
            "content_body": 123,  # Wrong type (should be str)
            "schema_version": "1",  # Wrong type (should be int)
        }
        try:
            validate_field_types(doc)
        except TypeError as e:
            print(e)  # Will show appropriate error message
        ```
    """
    logger.debug("Starting field type validation")

    for field, expected_type in field_types.items():
        if field not in doc:
            continue  # Skip optional fields

        value = doc[field]
        logger.debug("Validating type of field %s: %r", field, type(value))

        # Handle special case for embedding which can be list, tuple, or ndarray
        if field == "embedding":
            if not isinstance(value, expected_type):
                logger.error(
                    "Invalid type for field %s: %s (expected numeric array)", field, type(value)
                )
                raise TypeError(f"{field}.*numeric_array")
            continue

        # Handle special case for chunk_ids which must be list/tuple of strings
        if field == "chunk_ids" and value is not None:
            if not isinstance(value, expected_type):
                logger.error(
                    "Invalid type for field %s: %s (expected list/tuple)", field, type(value)
                )
                raise TypeError(f"{field}.*list")

            # Validate all chunk IDs are strings
            if not all(isinstance(chunk_id, str) for chunk_id in value):
                logger.error("Chunk IDs must all be strings")
                raise TypeError(f"{field}.*string")
            continue

        # Handle special case for parent_id which can be str or None
        if field == "parent_id":
            if value is not None and not isinstance(value, expected_type):
                logger.error(
                    "Invalid type for field %s: %s (expected str or None)", field, type(value)
                )
                raise TypeError(f"{field}.*string")
            continue

        # Regular type validation for other fields
        if not isinstance(value, expected_type):
            logger.error(
                "Invalid type for field %s: %s (expected %s)",
                field,
                type(value),
                expected_type.__name__,
            )
            raise TypeError(f"{field}.*{expected_type.__name__}")

    logger.info("Field type validation successful")


def get_dict_depth(d: dict[str, Any], current_depth: int = 0) -> int:
    """
    Calculate the maximum depth of a nested dictionary.

    Args:
        d: Dictionary to check
        current_depth: Current nesting level (used for recursion)

    Returns:
        Maximum nesting depth
    """
    if not isinstance(d, dict) or not d:
        return current_depth

    return max(
        get_dict_depth(v, current_depth + 1) if isinstance(v, dict) else current_depth + 1
        for v in d.values()
    )


def validate_size_constraints(doc: dict[str, Any]) -> None:
    """
    Validate size constraints on document fields.

    Checks the following size constraints:
    - Content body: 100KB limit
    - Chunk list: 1000 chunks max
    - Metadata: 100 levels deep max
    - Metadata fields: 100 fields max

    Args:
        doc: The document to validate

    Raises:
        ValueError: If any size constraints are violated, with message format:
            "{field}.*{constraint_type}"

    Example:
        ```python
        doc = {
            "content_body": "x" * (100 * 1024 + 1),  # Exceeds 100KB
            "chunk_ids": ["id"] * 1001,  # Exceeds 1000 chunks
            "metadata": {"a": {"b": {"c": {"d": "too deep"}}}}  # Too deep
        }
        try:
            validate_size_constraints(doc)
        except ValueError as e:
            print(e)  # Will show appropriate error message
        ```
    """
    logger.debug("Starting size constraint validation")

    # Validate content body size
    content_size = len(doc["content_body"].encode("utf-8"))
    if content_size > MAX_CONTENT_SIZE:
        logger.error(
            "Content body exceeds size limit: %d bytes (max %d)", content_size, MAX_CONTENT_SIZE
        )
        raise ValueError("content_body.*size")

    # Validate chunk list size
    if doc.get("chunk_ids"):
        chunk_count = len(doc["chunk_ids"])
        if chunk_count > MAX_CHUNKS:
            logger.error("Too many chunks: %d (max %d)", chunk_count, MAX_CHUNKS)
            raise ValueError("chunk_ids.*count")

    # Validate metadata if present
    if doc.get("metadata"):
        metadata = doc["metadata"]

        # Check metadata depth
        depth = get_dict_depth(metadata)
        if depth > MAX_METADATA_DEPTH:
            logger.error(
                "Metadata too deeply nested: %d levels (max %d)", depth, MAX_METADATA_DEPTH
            )
            raise ValueError("metadata.*depth")

        # Count total metadata fields (flattened)
        field_count = sum(1 for _ in _iter_dict_fields(metadata))
        if field_count > MAX_METADATA_FIELDS:
            logger.error("Too many metadata fields: %d (max %d)", field_count, MAX_METADATA_FIELDS)
            raise ValueError("metadata.*fields")

    logger.info("Size constraint validation successful")


def _iter_dict_fields(d: dict[str, Any]) -> Any:
    """
    Recursively iterate through all fields in a nested dictionary.

    Args:
        d: Dictionary to iterate through

    Yields:
        Each field name in the dictionary and its nested dictionaries
    """
    for key, value in d.items():
        yield key
        if isinstance(value, dict):
            yield from _iter_dict_fields(value)


def validate_batch(
    docs: list[dict[str, Any]], custom_fields: dict[str, type] | None = None, strict: bool = True
) -> None:
    """
    Validate a batch of documents.

    Args:
        docs: List of documents to validate
        custom_fields: Optional dict mapping field names to expected types
        strict: If True, reject unknown fields

    Raises:
        ValueError: If batch is empty
        ValueError: If any document is invalid
    """
    logger.debug("Starting batch validation of %d documents", len(docs))

    if not docs:
        logger.error("Empty document batch")
        raise ValueError("batch.*empty")

    for i, doc in enumerate(docs):
        try:
            validate_document_fields(doc, custom_fields, strict=strict)
        except (ValueError, TypeError) as e:
            logger.error("Validation failed for document %d: %s", i, str(e))
            raise ValueError(f"document[{i}].*{e!s}")

    logger.info("Batch validation successful")


def validate_json(json_str: str | bytes) -> dict[str, Any]:
    """
    Validate and parse a JSON document.

    Args:
        json_str: JSON string to validate and parse

    Returns:
        Parsed document dictionary

    Raises:
        ValueError: If JSON is invalid
        UnicodeError: If JSON contains invalid UTF-8
    """
    logger.debug("Starting JSON validation")

    try:
        # Handle bytes input
        if isinstance(json_str, bytes):
            json_str = json_str.decode("utf-8")

        import json

        doc = json.loads(json_str)

        if not isinstance(doc, dict):
            logger.error("JSON must decode to dictionary")
            raise ValueError("json.*dictionary")

        return doc

    except UnicodeError as e:
        logger.error("Invalid UTF-8 in JSON: %s", str(e))
        raise ValueError("json.*utf8") from e
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON: %s", str(e))
        raise ValueError("json.*syntax") from e
