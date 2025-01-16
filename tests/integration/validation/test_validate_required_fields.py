"""Tests for validating required fields in schema integration.

This module contains tests that verify the validation of required fields
when integrating the Core Schema System with Document Processing Schema.
"""
from copy import deepcopy

import pytest

from src.indexing.schema import SchemaValidator


def test_content_body_required(valid_document):
    """Test that content_body is a required field and cannot be None or empty."""
    doc = deepcopy(valid_document)
    del doc['content_body']
    with pytest.raises(ValueError, match='content_body.*required'):
        SchemaValidator.validate_object(doc)
    doc['content_body'] = None
    with pytest.raises(ValueError, match='content_body.*required'):
        SchemaValidator.validate_object(doc)
    doc['content_body'] = ''
    with pytest.raises(ValueError, match='content_body.*empty'):
        SchemaValidator.validate_object(doc)


def test_timestamp_utc_required(valid_document):
    """Test that timestamp_utc is required and must be in valid ISO format."""
    doc = deepcopy(valid_document)
    del doc['timestamp_utc']
    with pytest.raises(ValueError, match='timestamp_utc.*required'):
        SchemaValidator.validate_object(doc)
    doc['timestamp_utc'] = '2024-01-20'
    with pytest.raises(ValueError, match='timestamp_utc.*ISO'):
        SchemaValidator.validate_object(doc)


def test_schema_version_required(valid_document):
    """Test that schema_version is required and must be a positive integer."""
    doc = deepcopy(valid_document)
    del doc['schema_version']
    with pytest.raises(ValueError, match='schema_version.*required'):
        SchemaValidator.validate_object(doc)
    doc['schema_version'] = '1'
    with pytest.raises(TypeError, match='schema_version.*integer'):
        SchemaValidator.validate_object(doc)
    doc['schema_version'] = -1
    with pytest.raises(ValueError, match='schema_version.*positive'):
        SchemaValidator.validate_object(doc)


def test_embedding_required(valid_document):
    """Test that embedding is required and must be a list of correct dimension."""
    doc = deepcopy(valid_document)
    del doc['embedding']
    with pytest.raises(ValueError, match='embedding.*required'):
        SchemaValidator.validate_object(doc)
    doc['embedding'] = [0.1] * 100
    with pytest.raises(ValueError, match='embedding.*dimension'):
        SchemaValidator.validate_object(doc)
    doc['embedding'] = ['not_a_number'] * 384
    with pytest.raises(TypeError, match='embedding.*numeric'):
        SchemaValidator.validate_object(doc)