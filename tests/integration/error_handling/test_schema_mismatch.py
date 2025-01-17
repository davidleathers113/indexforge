"""Tests for schema mismatch handling in schema integration.

This module contains tests that verify the proper handling of mismatches
between document schemas and expected schemas.
"""

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

import pytest

from src.core.processors.base import BaseProcessor
from src.indexing.schema import SchemaDefinition, SchemaValidator


def create_valid_document() -> dict[str, Any]:
    """Create a valid test document."""
    return {
        "content_body": "Test content",
        "content_summary": "Summary",
        "content_title": "Title",
        "schema_version": 1,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "parent_id": None,
        "chunk_ids": [],
        "embedding": [0.1] * 384,
    }


def test_incompatible_schema_versions():
    """Test handling of incompatible schema versions between systems."""
    doc = create_valid_document()
    doc["schema_version"] = SchemaDefinition.CURRENT_VERSION + 1
    with pytest.raises(ValueError, match="incompatible.*version"):
        SchemaValidator.validate_object(doc)


def test_field_definition_mismatch():
    """Test handling of mismatched field definitions."""
    doc = create_valid_document()
    doc["unknown_field"] = "value"
    doc["custom_field"] = 123
    with pytest.raises(ValueError, match="unknown.*field"):
        SchemaValidator.validate_object(doc, strict=True)


def test_field_type_mismatch():
    """Test handling of mismatched field types."""
    doc = create_valid_document()
    type_mismatches = [
        ("content_body", 123),
        ("schema_version", "1"),
        ("chunk_ids", "not_a_list"),
        ("embedding", "not_a_vector"),
    ]
    for field, value in type_mismatches:
        test_doc = deepcopy(doc)
        test_doc[field] = value
        with pytest.raises(TypeError, match=f"{field}.*type"):
            SchemaValidator.validate_object(test_doc)


def test_metadata_schema_mismatch():
    """Test handling of mismatched metadata schemas."""
    doc = create_valid_document()
    invalid_metadata = [
        {"key": "value"},
        123,
        "string_metadata",
        {"nested": {"too": {"deep": {"for": "schema"}}}},
    ]
    for metadata in invalid_metadata:
        test_doc = deepcopy(doc)
        test_doc["metadata"] = metadata
        with pytest.raises((TypeError, ValueError)):
            SchemaValidator.validate_object(test_doc)


def test_embedding_dimension_mismatch():
    """Test handling of mismatched embedding dimensions."""
    doc = create_valid_document()
    wrong_dimensions = [[0.1] * 128, [0.1] * 512, [], [0.1]]
    for embedding in wrong_dimensions:
        test_doc = deepcopy(doc)
        test_doc["embedding"] = embedding
        with pytest.raises(ValueError, match="embedding.*dimension"):
            SchemaValidator.validate_object(test_doc)


def test_processor_schema_mismatch():
    """Test handling of mismatches between processor and core schema."""
    processor = BaseProcessor()
    processor_doc = {
        "content": {"body": "Test content", "metadata": {"format": "unknown"}},
        "source": {"type": "unsupported", "location": "unknown"},
    }
    with pytest.raises(ValueError, match="processor.*schema"):
        processor.process_and_map(processor_doc)


def test_relationship_schema_mismatch():
    """Test handling of mismatched relationship schemas."""
    doc = create_valid_document()
    invalid_relationships = [
        {"parent_id": [1, 2, 3]},
        {"chunk_ids": "chunk1"},
        {"parent_id": {"id": "parent1"}},
        {"chunk_ids": [1, "2", 3.0]},
    ]
    for relationships in invalid_relationships:
        test_doc = deepcopy(doc)
        test_doc.update(relationships)
        with pytest.raises((TypeError, ValueError)):
            SchemaValidator.validate_object(test_doc)


def test_timestamp_format_mismatch():
    """Test handling of mismatched timestamp formats."""
    doc = create_valid_document()
    invalid_timestamps = [
        "2024-01-20",
        "12:00:00",
        "2024-01-20 12:00:00",
        "2024-13-45T25:61:61Z",
        datetime.now().timestamp(),
    ]
    for timestamp in invalid_timestamps:
        test_doc = deepcopy(doc)
        test_doc["timestamp_utc"] = timestamp
        with pytest.raises(ValueError, match="timestamp.*format"):
            SchemaValidator.validate_object(test_doc)


def test_content_format_mismatch():
    """Test handling of mismatched content formats."""
    doc = create_valid_document()
    invalid_contents = [
        b"binary data",
        ["content", "in", "list"],
        {"content": "in_dict"},
        123,
        True,
    ]
    for content in invalid_contents:
        test_doc = deepcopy(doc)
        test_doc["content_body"] = content
        with pytest.raises(TypeError, match="content.*string"):
            SchemaValidator.validate_object(test_doc)
