"""Tests for reference caching functionality.

These tests verify the caching of references, including cache hits/misses,
invalidation, and performance monitoring.
"""
from uuid import uuid4

import pytest

from src.utils.chunking.reference_cache import ReferenceCache
from src.utils.chunking.references import ReferenceManager, ReferenceType


@pytest.fixture
def ref_manager():
    """Create a reference manager with test references."""
    manager = ReferenceManager()
    chunk1 = manager.add_chunk('Source chunk')
    chunk2 = manager.add_chunk('Target chunk')
    chunk3 = manager.add_chunk('Another chunk')
    manager.add_reference(chunk1, chunk2, ReferenceType.CITATION)
    manager.add_reference(chunk2, chunk3, ReferenceType.SIMILAR)
    manager.add_reference(chunk1, chunk3, ReferenceType.RELATED)
    return manager

@pytest.fixture
def reference_cache(ref_manager):
    """Create a reference cache with test reference manager."""
    return ReferenceCache(ref_manager, maxsize=100)

def test_cache_hit(reference_cache):
    """Test successful cache hits."""
    source_id = next(iter(reference_cache.ref_manager._chunks.keys()))
    target_id = next(iter(reference_cache.ref_manager._chunks.values())).id
    ref1 = reference_cache.get_reference(source_id, target_id)
    assert ref1 is not None
    assert reference_cache.stats.hits == 0
    assert reference_cache.stats.misses == 1
    ref2 = reference_cache.get_reference(source_id, target_id)
    assert ref2 is not None
    assert reference_cache.stats.hits == 1
    assert reference_cache.stats.misses == 1
    assert ref1 is ref2

def test_cache_miss(reference_cache):
    """Test cache misses for non-existent references."""
    unknown_id = uuid4()
    ref = reference_cache.get_reference(unknown_id, unknown_id)
    assert ref is None
    assert reference_cache.stats.hits == 0
    assert reference_cache.stats.misses == 1

def test_cache_invalidation(reference_cache):
    """Test reference invalidation."""
    source_id = next(iter(reference_cache.ref_manager._chunks.keys()))
    target_id = next(iter(reference_cache.ref_manager._chunks.values())).id
    ref1 = reference_cache.get_reference(source_id, target_id)
    assert ref1 is not None
    reference_cache.invalidate_reference(source_id, target_id)
    assert reference_cache.stats.invalidations == 1
    ref2 = reference_cache.get_reference(source_id, target_id)
    assert ref2 is not None
    assert reference_cache.stats.misses == 2

def test_chunk_reference_invalidation(reference_cache):
    """Test invalidation of all references for a chunk."""
    source_id = next(iter(reference_cache.ref_manager._chunks.keys()))
    refs = reference_cache.get_chunk_references(source_id)
    assert len(refs) > 0
    reference_cache.invalidate_chunk_references(source_id)
    assert source_id not in reference_cache.forward_index
    assert source_id not in reference_cache.reverse_index

def test_bidirectional_reference_caching(reference_cache):
    """Test caching of bidirectional references."""
    chunk1 = reference_cache.ref_manager.add_chunk('Chunk 1')
    chunk2 = reference_cache.ref_manager.add_chunk('Chunk 2')
    reference_cache.ref_manager.add_reference(chunk1, chunk2, ReferenceType.SIMILAR, bidirectional=True)
    ref1 = reference_cache.get_reference(chunk1, chunk2)
    assert ref1 is not None
    assert ref1.bidirectional
    ref2 = reference_cache.get_reference(chunk2, chunk1)
    assert ref2 is not None
    assert reference_cache.stats.hits == 1

def test_cache_size_limit():
    """Test cache respects maximum size limit."""
    manager = ReferenceManager()
    cache = ReferenceCache(manager, maxsize=2)
    chunk_ids = [manager.add_chunk(f'Chunk {i}') for i in range(4)]
    for i in range(3):
        manager.add_reference(chunk_ids[i], chunk_ids[i + 1], ReferenceType.SIMILAR)
    for i in range(3):
        cache.get_reference(chunk_ids[i], chunk_ids[i + 1])
    assert len(cache.reference_cache) <= 2

def test_cache_stats(reference_cache):
    """Test cache statistics tracking."""
    source_id = next(iter(reference_cache.ref_manager._chunks.keys()))
    target_id = next(iter(reference_cache.ref_manager._chunks.values())).id
    reference_cache.get_reference(source_id, target_id)
    reference_cache.get_reference(source_id, target_id)
    reference_cache.get_reference(uuid4(), uuid4())
    reference_cache.invalidate_reference(source_id, target_id)
    stats = reference_cache.get_stats()
    assert stats.hits == 1
    assert stats.misses == 2
    assert stats.invalidations == 1
    assert stats.total_requests == 3
    assert 0 <= stats.hit_rate <= 100

def test_clear_cache(reference_cache):
    """Test clearing the cache."""
    source_id = next(iter(reference_cache.ref_manager._chunks.keys()))
    refs = reference_cache.get_chunk_references(source_id)
    assert len(refs) > 0
    reference_cache.clear()
    assert len(reference_cache.reference_cache) == 0
    assert len(reference_cache.forward_index) == 0
    assert len(reference_cache.reverse_index) == 0
    assert reference_cache.stats.hits == 0
    assert reference_cache.stats.misses == 0
    assert reference_cache.stats.invalidations == 0