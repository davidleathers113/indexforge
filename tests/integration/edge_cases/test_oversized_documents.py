"""Tests for handling oversized documents and content.

This module contains tests that verify the handling of documents that exceed
normal size limits, including large content bodies and embeddings.
"""
from typing import Any, Dict

import pytest

from src.indexing.schema import SchemaValidator


def create_base_document() -> Dict[str, Any]:
    """Create a base test document."""
    return {'content_body': 'Test content', 'schema_version': 1, 'timestamp_utc': '2024-01-20T12:00:00Z', 'parent_id': None, 'chunk_ids': [], 'embedding': [0.1] * 384}

def test_oversized_content_body():
    """Test handling of documents with extremely large content bodies."""
    doc = create_base_document()
    large_content = 'test ' * 100000
    doc['content_body'] = large_content
    with pytest.raises(ValueError, match='content.*size.*exceeded'):
        SchemaValidator.validate_object(doc)

def test_oversized_embedding():
    """Test handling of documents with incorrect embedding dimensions."""
    doc = create_base_document()
    doc['embedding'] = [0.1] * 1000
    with pytest.raises(ValueError, match='embedding.*dimension'):
        SchemaValidator.validate_object(doc)
    doc['embedding'] = [0.1] * 100
    with pytest.raises(ValueError, match='embedding.*dimension'):
        SchemaValidator.validate_object(doc)

def test_large_chunk_list():
    """Test handling of documents with an excessive number of chunks."""
    doc = create_base_document()
    doc['chunk_ids'] = [f'chunk_{i}' for i in range(10000)]
    with pytest.raises(ValueError, match='chunks.*limit'):
        SchemaValidator.validate_object(doc)

def test_deep_metadata_nesting():
    """Test handling of documents with deeply nested metadata."""
    doc = create_base_document()
    nested_metadata = {}
    current = nested_metadata
    for i in range(100):
        current['nested'] = {}
        current = current['nested']
    doc['metadata'] = nested_metadata
    with pytest.raises(ValueError, match='metadata.*nesting'):
        SchemaValidator.validate_object(doc)

def test_large_metadata_object():
    """Test handling of documents with very large metadata objects."""
    doc = create_base_document()
    doc['metadata'] = {f'field_{i}': f'value_{i}' for i in range(10000)}
    with pytest.raises(ValueError, match='metadata.*size'):
        SchemaValidator.validate_object(doc)

def test_large_batch_processing():
    """Test handling of very large batches of documents."""
    docs = [create_base_document() for _ in range(10000)]
    with pytest.raises(ValueError, match='batch.*size'):
        SchemaValidator.validate_batch(docs)

def test_content_with_special_characters():
    """Test handling of content with a high proportion of special characters."""
    doc = create_base_document()
    special_chars = ''.join([chr(i) for i in range(32, 127)])
    doc['content_body'] = special_chars * 1000
    SchemaValidator.validate_object(doc)

def test_binary_content_handling():
    """Test handling of content with binary data."""
    doc = create_base_document()
    binary_data = bytes([i % 256 for i in range(1000)])
    doc['content_body'] = binary_data.decode('utf-8', errors='ignore')
    with pytest.raises(ValueError, match='invalid.*characters'):
        SchemaValidator.validate_object(doc)

def test_maximum_valid_sizes():
    """Test documents that are exactly at the maximum allowed sizes."""
    doc = create_base_document()
    doc['content_body'] = 'test ' * 25000
    doc['chunk_ids'] = [f'chunk_{i}' for i in range(1000)]
    doc['metadata'] = {f'field_{i}': f'value_{i}' for i in range(100)}
    SchemaValidator.validate_object(doc)

def test_unicode_content_handling():
    """Test handling of content with various Unicode characters."""
    doc = create_base_document()
    unicode_content = ''.join(['Hello', '你好', '안녕하세요', 'こんにちは', '🌍🌎🌏']) * 1000
    doc['content_body'] = unicode_content
    SchemaValidator.validate_object(doc)