"""Performance tests for semantic relationship detection and topic clustering.

These tests evaluate the system's performance with large-scale data,
measuring execution time, memory usage, and scalability.
"""
import time
from typing import Set
from uuid import UUID

from memory_profiler import profile
import pytest


@pytest.fixture
def large_chunk_set(semantic_processor) -> Set[UUID]:
    """Create a large set of chunks for performance testing."""
    topics = ['technology', 'science', 'art', 'history', 'business']
    subtopics = ['research', 'development', 'analysis', 'theory', 'practice']
    terms = ['data', 'system', 'process', 'method', 'model']
    chunk_ids = set()
    for topic in topics:
        for subtopic in subtopics:
            for term in terms:
                content = f'{topic} {subtopic} {term} ' * 10
                chunk_id = semantic_processor.ref_manager.add_chunk(content)
                chunk_ids.add(chunk_id)
    return chunk_ids

def test_embedding_cache_performance(semantic_processor, large_chunk_set):
    """Test embedding cache performance with large datasets."""
    start_time = time.time()
    cache_hits = 0
    for chunk_id in large_chunk_set:
        semantic_processor.get_chunk_embedding(chunk_id)
    first_pass_time = time.time() - start_time
    start_time = time.time()
    for chunk_id in large_chunk_set:
        if chunk_id in semantic_processor._embedding_cache:
            cache_hits += 1
        semantic_processor.get_chunk_embedding(chunk_id)
    second_pass_time = time.time() - start_time
    assert cache_hits == len(large_chunk_set)
    assert second_pass_time < first_pass_time * 0.1

@profile
def test_memory_usage_clustering(semantic_processor, large_chunk_set):
    """Test memory usage during topic clustering."""
    _ = semantic_processor.analyze_topic_relationships(large_chunk_set, num_topics=10)
    additional_chunks = set()
    for i in range(100):
        content = f'additional content {i} ' * 20
        chunk_id = semantic_processor.ref_manager.add_chunk(content)
        additional_chunks.add(chunk_id)
    _ = semantic_processor.analyze_topic_relationships(large_chunk_set | additional_chunks, num_topics=15)

def test_clustering_performance_scaling(semantic_processor):
    """Test how clustering performance scales with dataset size."""
    dataset_sizes = [10, 50, 100, 200]
    timings = []
    for size in dataset_sizes:
        chunks = set()
        for i in range(size):
            content = f'content {i} with some variation ' * 10
            chunk_id = semantic_processor.ref_manager.add_chunk(content)
            chunks.add(chunk_id)
        start_time = time.time()
        _ = semantic_processor.analyze_topic_relationships(chunks, num_topics=min(size // 5, 20))
        timings.append(time.time() - start_time)
    for i in range(len(dataset_sizes) - 1):
        size_ratio = dataset_sizes[i + 1] / dataset_sizes[i]
        time_ratio = timings[i + 1] / timings[i]
        assert time_ratio < size_ratio ** 2

def test_parallel_reference_creation(semantic_processor, large_chunk_set):
    """Test performance of creating references for multiple chunks."""
    chunk_list = list(large_chunk_set)
    batch_size = 10
    timings = []
    for i in range(0, len(chunk_list), batch_size):
        batch = chunk_list[i:i + batch_size]
        start_time = time.time()
        for chunk_id in batch:
            semantic_processor.create_semantic_references(chunk_id)
        timings.append(time.time() - start_time)
    avg_time = sum(timings) / len(timings)
    assert all((abs(t - avg_time) < avg_time * 0.5 for t in timings))

def test_tfidf_performance(semantic_processor, large_chunk_set):
    """Test TF-IDF computation performance for topic labeling."""
    start_time = time.time()
    chunk_texts = [semantic_processor.ref_manager._chunks[chunk_id].content for chunk_id in large_chunk_set]
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer(max_features=10, stop_words='english')
    _ = vectorizer.fit_transform(chunk_texts)
    tfidf_time = time.time() - start_time
    assert tfidf_time < len(large_chunk_set) * 0.01