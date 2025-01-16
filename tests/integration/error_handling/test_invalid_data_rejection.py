"""Tests for invalid data rejection in schema integration.

This module contains tests that verify the proper rejection of invalid
data during schema validation and processing.
"""
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

import pytest

from src.indexing.schema import SchemaValidator


def create_valid_document() -> dict[str, Any]:
    """Create a valid test document."""
    return {'content_body': 'Test content', 'content_summary': 'Summary', 'content_title': 'Title', 'schema_version': 1, 'timestamp_utc': datetime.now(UTC).isoformat(), 'parent_id': None, 'chunk_ids': [], 'embedding': [0.1] * 384}


def test_invalid_field_types():
    """Test rejection of documents with invalid field types."""
    doc = create_valid_document()
    doc['schema_version'] = '1'
    with pytest.raises(TypeError, match='schema_version.*integer'):
        SchemaValidator.validate_object(doc)
    doc = create_valid_document()
    doc['timestamp_utc'] = 12345
    with pytest.raises(TypeError, match='timestamp.*string'):
        SchemaValidator.validate_object(doc)
    doc = create_valid_document()
    doc['chunk_ids'] = 'not_a_list'
    with pytest.raises(TypeError, match='chunk_ids.*list'):
        SchemaValidator.validate_object(doc)


def test_invalid_field_values():
    """Test rejection of documents with invalid field values."""
    doc = create_valid_document()
    doc['schema_version'] = -1
    with pytest.raises(ValueError, match='schema_version.*positive'):
        SchemaValidator.validate_object(doc)
    doc = create_valid_document()
    doc['timestamp_utc'] = 'not_a_timestamp'
    with pytest.raises(ValueError, match='timestamp.*format'):
        SchemaValidator.validate_object(doc)
    doc = create_valid_document()
    doc['embedding'] = ['not_a_number'] * 384
    with pytest.raises(TypeError, match='embedding.*numeric'):
        SchemaValidator.validate_object(doc)


def test_missing_required_fields():
    """Test rejection of documents with missing required fields."""
    doc = create_valid_document()
    required_fields = ['content_body', 'schema_version', 'timestamp_utc', 'embedding']
    for field in required_fields:
        test_doc = deepcopy(doc)
        del test_doc[field]
        with pytest.raises(ValueError, match=f'{field}.*required'):
            SchemaValidator.validate_object(test_doc)


def test_empty_required_fields():
    """Test rejection of documents with empty required fields."""
    doc = create_valid_document()
    doc['content_body'] = ''
    with pytest.raises(ValueError, match='content_body.*empty'):
        SchemaValidator.validate_object(doc)
    doc = create_valid_document()
    doc['embedding'] = []
    with pytest.raises(ValueError, match='embedding.*empty'):
        SchemaValidator.validate_object(doc)


def test_invalid_metadata_values():
    """Test rejection of documents with invalid metadata values."""
    doc = create_valid_document()
    doc['metadata'] = 'not_an_object'
    with pytest.raises(TypeError, match='metadata.*object'):
        SchemaValidator.validate_object(doc)
    doc['metadata'] = {'numeric_field': 'not_a_number', 'date_field': 'not_a_date'}
    with pytest.raises(TypeError, match='metadata.*type'):
        SchemaValidator.validate_object(doc)


def test_invalid_relationship_references():
    """Test rejection of documents with invalid relationship references."""
    doc = create_valid_document()
    doc['parent_id'] = 12345
    with pytest.raises(TypeError, match='parent_id.*string'):
        SchemaValidator.validate_object(doc)
    doc = create_valid_document()
    doc['chunk_ids'] = [1, 2, 3]
    with pytest.raises(TypeError, match='chunk_ids.*string'):
        SchemaValidator.validate_object(doc)


def test_schema_version_mismatch():
    """Test rejection of documents with mismatched schema versions."""
    doc = create_valid_document()
    doc['schema_version'] = 9999
    with pytest.raises(ValueError, match='schema_version.*unsupported'):
        SchemaValidator.validate_object(doc)
    doc['schema_version'] = 0
    with pytest.raises(ValueError, match='schema_version.*positive'):
        SchemaValidator.validate_object(doc)


def test_malformed_json():
    """Test rejection of malformed JSON input."""
    invalid_json = "{'not': 'valid', json}"
    with pytest.raises(ValueError, match='invalid.*JSON'):
        SchemaValidator.validate_json(invalid_json)
    partial_json = '{"content_body": "test"'
    with pytest.raises(ValueError, match='invalid.*JSON'):
        SchemaValidator.validate_json(partial_json)


def test_invalid_utf8_content():
    """Test rejection of content with invalid UTF-8 encoding."""
    doc = create_valid_document()
    doc['content_body'] = b'invalid \xff utf-8'.decode('utf-8', errors='ignore')
    with pytest.raises(ValueError, match='invalid.*encoding'):
        SchemaValidator.validate_object(doc)