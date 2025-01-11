"""Tests for performance and scalability in schema integration.

This module contains tests that verify the performance characteristics
of schema operations under various load conditions.
"""
import time
from copy import deepcopy
from typing import Any, Dict, List
import pytest
from src.indexing.schema import SchemaDefinition, SchemaValidator

def generate_large_document_set(count: int) -> List[Dict[str, Any]]:
    """Generate a large set of test documents."""
    base_doc = {'schema_version': 1, 'timestamp_utc': '2024-01-20T12:00:00Z', 'parent_id': None, 'chunk_ids': []}
    docs = []
    for i in range(count):
        doc = deepcopy(base_doc)
        doc['content_body'] = f'Test document {i} with some meaningful content for testing'
        doc['embedding'] = [0.1] * 384
        docs.append(doc)
    return docs

@pytest.mark.performance
def test_batch_validation_performance():
    """Test validation performance with large batches of documents."""
    batch_sizes = [100, 1000, 10000]
    times = {}
    for size in batch_sizes:
        docs = generate_large_document_set(size)
        start_time = time.time()
        for doc in docs:
            SchemaValidator.validate_object(doc)
        end_time = time.time()
        times[size] = end_time - start_time
        if size > 100:
            expected_time = times[100] * (size / 100)
            assert times[size] < expected_time * 1.5

@pytest.mark.performance
def test_vector_cache_performance(base_schema):
    """Test performance impact of vector cache settings."""
    docs = generate_large_document_set(1000)
    query = 'test query for performance measurement'
    cache_sizes = [100, 500, 1000]
    times = {}
    for cache_size in cache_sizes:
        base_schema.config.vector_cache_max_objects = cache_size
        start_time = time.time()
        results = base_schema.search(query=query, documents=docs, hybrid_alpha=0.5)
        end_time = time.time()
        times[cache_size] = end_time - start_time
        assert len(results) > 0
        if cache_size > 100:
            assert times[cache_size] <= times[100]

@pytest.mark.performance
def test_index_construction_performance():
    """Test performance of index construction with different parameters."""
    docs = generate_large_document_set(1000)
    ef_values = [64, 128, 256]
    times = {}
    for ef in ef_values:
        schema = SchemaDefinition.get_schema(ef_construction=ef, max_connections=32)
        start_time = time.time()
        schema.build_index(docs)
        end_time = time.time()
        times[ef] = end_time - start_time
        if ef > 64:
            assert times[ef] > times[64]

@pytest.mark.performance
def test_memory_usage_under_load():
    """Test memory usage with large document sets."""
    import os
    import psutil
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    docs = generate_large_document_set(10000)
    for doc in docs[:1000]:
        SchemaValidator.validate_object(doc)
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    assert memory_increase < 10 * 1024 * 1024

@pytest.mark.performance
def test_concurrent_query_performance(base_schema):
    """Test performance with concurrent search queries."""
    import concurrent.futures
    docs = generate_large_document_set(1000)
    queries = ['test query 1', 'test query 2', 'test query 3', 'test query 4']

    def search_query(query: str) -> List[Dict[str, Any]]:
        return base_schema.search(query=query, documents=docs, hybrid_alpha=0.5)
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_query = {executor.submit(search_query, query): query for query in queries}
        results = []
        for future in concurrent.futures.as_completed(future_to_query):
            query = future_to_query[future]
            query_results = future.result()
            results.append((query, query_results))
            assert len(query_results) > 0
    end_time = time.time()
    total_time = end_time - start_time
    assert len(results) == len(queries)
    sequential_time = sum((len(base_schema.search(q, docs, 0.5)) for q in queries))
    assert total_time < sequential_time