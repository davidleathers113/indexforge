"""Tests for hybrid search functionality in schema integration.

This module contains tests that verify the hybrid search capabilities
(BM25 + vector similarity) when integrating Core Schema System with
Document Processing Schema.
"""
from copy import deepcopy
from typing import Any

from src.utils.text_processing import generate_embeddings


def create_test_documents() -> list[dict[str, Any]]:
    """Helper function to create a set of test documents with varied content."""
    base_doc = {'schema_version': 1, 'timestamp_utc': '2024-01-20T12:00:00Z', 'parent_id': None, 'chunk_ids': []}
    docs = []
    test_contents = ['Machine learning is a subset of artificial intelligence', 'Deep learning uses neural networks for pattern recognition', 'Natural language processing helps computers understand text', 'Computer vision focuses on image and video analysis']
    for content in test_contents:
        doc = deepcopy(base_doc)
        doc['content_body'] = content
        doc['embedding'] = generate_embeddings(content).tolist()
        docs.append(doc)
    return docs


def test_exact_keyword_match(base_schema):
    """Test that exact keyword matches are found with high BM25 scores."""
    docs = create_test_documents()
    query = 'neural networks'
    results = base_schema.search(query=query, documents=docs, hybrid_alpha=0.5)
    assert any('neural networks' in doc['content_body'].lower() for doc in results[:2])


def test_semantic_similarity_match(base_schema):
    """Test that semantically similar content is found with high vector similarity."""
    docs = create_test_documents()
    query = 'AI and ML technologies'
    results = base_schema.search(query=query, documents=docs, hybrid_alpha=0.5)
    assert any('machine learning' in doc['content_body'].lower() and 'artificial intelligence' in doc['content_body'].lower() for doc in results[:2])


def test_hybrid_search_weighting(base_schema):
    """Test that hybrid search weights affect result ranking appropriately."""
    docs = create_test_documents()
    query = 'computer understanding'
    bm25_results = base_schema.search(query=query, documents=docs, hybrid_alpha=0.9)
    vector_results = base_schema.search(query=query, documents=docs, hybrid_alpha=0.1)
    assert bm25_results[0] != vector_results[0]


def test_out_of_vocabulary_handling(base_schema):
    """Test handling of queries with out-of-vocabulary terms."""
    docs = create_test_documents()
    query = 'xyz123 machine learning'
    results = base_schema.search(query=query, documents=docs, hybrid_alpha=0.5)
    assert any('machine learning' in doc['content_body'].lower() for doc in results[:2])