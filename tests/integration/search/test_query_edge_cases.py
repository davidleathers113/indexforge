"""Tests for edge cases in search queries.

This module contains tests that verify the handling of edge cases
and unusual inputs in search queries.
"""
from copy import deepcopy
from typing import Any, Dict, List
import pytest
from src.indexing.schema import SchemaValidator
from src.utils.text_processing import generate_embeddings

def test_empty_query_handling(base_schema):
    """Test handling of empty search queries."""
    docs = [{'content_body': 'Test document content', 'schema_version': 1, 'timestamp_utc': '2024-01-20T12:00:00Z', 'embedding': [0.1] * 384}]
    with pytest.raises(ValueError, match='empty.*query'):
        base_schema.search(query='', documents=docs)
    with pytest.raises(ValueError, match='empty.*query'):
        base_schema.search(query='   ', documents=docs)
    with pytest.raises(ValueError, match='None.*query'):
        base_schema.search(query=None, documents=docs)

def test_malformed_query_handling(base_schema):
    """Test handling of malformed search queries."""
    docs = [{'content_body': 'Test document content', 'schema_version': 1, 'timestamp_utc': '2024-01-20T12:00:00Z', 'embedding': [0.1] * 384}]
    with pytest.raises(TypeError, match='string.*query'):
        base_schema.search(query=123, documents=docs)
    with pytest.raises(TypeError, match='string.*query'):
        base_schema.search(query=['test'], documents=docs)
    with pytest.raises(TypeError, match='string.*query'):
        base_schema.search(query={'text': 'test'}, documents=docs)

def test_missing_field_handling(base_schema):
    """Test search behavior with documents missing required fields."""
    docs = [{'content_body': 'Document with all fields', 'schema_version': 1, 'timestamp_utc': '2024-01-20T12:00:00Z', 'embedding': [0.1] * 384}, {'schema_version': 1, 'timestamp_utc': '2024-01-20T12:00:00Z', 'embedding': [0.1] * 384}, {'content_body': 'Document missing embedding', 'schema_version': 1, 'timestamp_utc': '2024-01-20T12:00:00Z'}]
    results = base_schema.search(query='document', documents=docs, hybrid_alpha=0.5)
    assert len(results) == 1
    assert 'content_body' in results[0]
    assert 'embedding' in results[0]

def test_mixed_query_types(base_schema):
    """Test handling of queries mixing different search types."""
    docs = [{'content_body': 'Machine learning document', 'schema_version': 1, 'timestamp_utc': '2024-01-20T12:00:00Z', 'embedding': generate_embeddings('AI and machine learning').tolist()}, {'content_body': 'Natural language processing', 'schema_version': 1, 'timestamp_utc': '2024-01-20T12:00:00Z', 'embedding': generate_embeddings('NLP and text analysis').tolist()}]
    keyword_results = base_schema.search(query='machine learning', documents=docs, hybrid_alpha=1.0)
    vector_results = base_schema.search(query='machine learning', documents=docs, hybrid_alpha=0.0)
    hybrid_results = base_schema.search(query='machine learning', documents=docs, hybrid_alpha=0.5)
    assert keyword_results != vector_results
    assert hybrid_results != keyword_results or hybrid_results != vector_results

def test_extreme_query_lengths(base_schema):
    """Test handling of extremely short and long queries."""
    docs = [{'content_body': 'Test document content', 'schema_version': 1, 'timestamp_utc': '2024-01-20T12:00:00Z', 'embedding': [0.1] * 384}]
    results_short = base_schema.search(query='a', documents=docs, hybrid_alpha=0.5)
    assert isinstance(results_short, list)
    long_query = 'test ' * 1000
    results_long = base_schema.search(query=long_query, documents=docs, hybrid_alpha=0.5)
    assert isinstance(results_long, list)

def test_special_character_handling(base_schema):
    """Test handling of queries with special characters."""
    docs = [{'content_body': 'Test @#$% document', 'schema_version': 1, 'timestamp_utc': '2024-01-20T12:00:00Z', 'embedding': [0.1] * 384}]
    results = base_schema.search(query='@#$% document', documents=docs, hybrid_alpha=0.5)
    assert len(results) > 0
    assert results[0]['content_body'] == 'Test @#$% document'