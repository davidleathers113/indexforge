"""Tests for backward compatibility in schema versioning.

This module contains tests that verify the backward compatibility
of schema versions when integrating Core Schema System with
Document Processing Schema.
"""
from copy import deepcopy
from datetime import datetime, timezone
import pytest
from src.indexing.schema import SchemaValidator

def test_old_schema_version_acceptance(valid_document, base_schema):
    """Test that documents with older schema versions are accepted."""
    doc = deepcopy(valid_document)
    current_version = base_schema['version']
    doc['schema_version'] = current_version - 1
    SchemaValidator.validate_object(doc)
    if current_version > 2:
        doc['schema_version'] = 1
        SchemaValidator.validate_object(doc)

def test_missing_new_fields_handled(valid_document, base_schema):
    """Test that documents missing newer optional fields are accepted."""
    doc = deepcopy(valid_document)
    doc['schema_version'] = base_schema['version'] - 1
    optional_new_fields = ['content_summary', 'content_title']
    for field in optional_new_fields:
        if field in doc:
            del doc[field]
    SchemaValidator.validate_object(doc)

def test_deprecated_fields_handled(valid_document, base_schema):
    """Test that documents with deprecated fields are handled correctly."""
    doc = deepcopy(valid_document)
    doc['schema_version'] = base_schema['version'] - 1
    doc['deprecated_field'] = 'old value'
    doc['legacy_timestamp'] = datetime.now(timezone.utc).isoformat()
    with pytest.warns(DeprecationWarning):
        SchemaValidator.validate_object(doc)

def test_field_type_evolution(valid_document, base_schema):
    """Test handling of fields whose types have evolved over versions."""
    doc = deepcopy(valid_document)
    doc['schema_version'] = base_schema['version'] - 1
    doc['timestamp_utc'] = '2024-01-20T12:00:00Z'
    validated_doc = SchemaValidator.validate_object(doc)
    assert isinstance(validated_doc['timestamp_utc'], str)
    assert 'Z' in validated_doc['timestamp_utc']