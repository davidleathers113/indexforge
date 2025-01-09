"""Tests for custom property mapping in schema integration.

This module contains tests that verify the mapping of custom properties
from Document Processing Schema to Core Schema System.
"""
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict
import pytest
from src.connectors.direct_documentation_indexing.processors import BaseProcessor
from src.indexing.schema import SchemaValidator

def test_source_metadata_mapping(mock_processor, valid_document):
    """Test mapping of source-specific metadata to core schema properties."""
    source_doc = {'content': {'full_text': 'Test content', 'summary': 'Test summary', 'title': 'Test title'}, 'metadata': {'source_type': 'word', 'author': 'John Doe', 'last_modified': datetime.now(timezone.utc).isoformat(), 'page_count': 5}}
    mock_processor.process.return_value = source_doc
    processor = BaseProcessor()
    processed_doc = processor.process_and_map(source_doc)
    assert processed_doc['content_body'] == source_doc['content']['full_text']
    assert processed_doc['content_summary'] == source_doc['content']['summary']
    assert processed_doc['content_title'] == source_doc['content']['title']
    assert processed_doc['metadata']['source_type'] == 'word'
    assert processed_doc['metadata']['author'] == 'John Doe'
    assert 'last_modified' in processed_doc['metadata']
    assert isinstance(processed_doc['metadata']['page_count'], int)

def test_custom_field_validation(mock_processor, valid_document):
    """Test validation of custom fields in mapped document."""
    doc = deepcopy(valid_document)
    doc['metadata'] = {'source_type': 'word', 'custom_field': 'custom value', 'numeric_field': 42}
    custom_fields = {'source_type': {'type': 'string', 'required': True}, 'custom_field': {'type': 'string'}, 'numeric_field': {'type': 'integer'}}
    SchemaValidator.validate_object(doc, custom_fields=custom_fields)

def test_array_field_mapping(mock_processor, valid_document):
    """Test mapping of array fields from source to core schema."""
    source_doc = {'content': {'full_text': 'Test content', 'sections': ['Section 1', 'Section 2', 'Section 3']}, 'metadata': {'source_type': 'word', 'tags': ['tag1', 'tag2'], 'categories': ['cat1', 'cat2']}}
    mock_processor.process.return_value = source_doc
    processor = BaseProcessor()
    processed_doc = processor.process_and_map(source_doc)
    assert isinstance(processed_doc['metadata']['tags'], list)
    assert isinstance(processed_doc['metadata']['categories'], list)
    assert len(processed_doc['metadata']['tags']) == 2
    assert len(processed_doc['metadata']['categories']) == 2

def test_nested_field_mapping(mock_processor, valid_document):
    """Test mapping of nested fields from source to core schema."""
    source_doc = {'content': {'full_text': 'Test content', 'metadata': {'formatting': {'font': 'Arial', 'size': 12}}}, 'metadata': {'source_type': 'word', 'document_info': {'created_by': 'John Doe', 'department': 'Engineering'}}}
    mock_processor.process.return_value = source_doc
    processor = BaseProcessor()
    processed_doc = processor.process_and_map(source_doc)
    assert 'formatting' in processed_doc['metadata']
    assert processed_doc['metadata']['formatting']['font'] == 'Arial'
    assert processed_doc['metadata']['document_info']['department'] == 'Engineering'