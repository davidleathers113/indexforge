"""Tests for reference system monitoring utilities.

These tests verify the functionality of monitoring tools for reference health,
performance, and cache metrics.
"""
import logging
import time

import pytest

from src.utils.chunking.monitoring import ReferenceMonitor, time_operation
from src.utils.chunking.reference_cache import ReferenceCache
from src.utils.chunking.reference_classifier import ReferenceClassifier
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


@pytest.fixture
def reference_classifier(ref_manager):
    """Create a reference classifier with test reference manager."""
    return ReferenceClassifier(ref_manager)


@pytest.fixture
def monitor(ref_manager, reference_cache, reference_classifier):
    """Create a reference monitor with test components."""
    return ReferenceMonitor(ref_manager, reference_cache, reference_classifier)


def test_health_check_normal(monitor):
    """Test health check with normal references."""
    metrics = monitor.check_reference_health()
    assert metrics.total_references == 3
    assert metrics.orphaned_references == 0
    assert metrics.circular_references == 0
    assert metrics.invalid_references == 0
    assert metrics.bidirectional_mismatches == 0


def test_health_check_orphaned_references(monitor):
    """Test health check with orphaned references."""
    source_id = next(iter(monitor.ref_manager._chunks.keys()))
    target_id = monitor.ref_manager.add_chunk('Orphan target')
    monitor.ref_manager.add_reference(source_id, target_id, ReferenceType.CITATION)
    del monitor.ref_manager._chunks[target_id]
    metrics = monitor.check_reference_health()
    assert metrics.orphaned_references > 0


def test_health_check_circular_references(monitor):
    """Test health check with circular references."""
    chunk1 = monitor.ref_manager.add_chunk('Chunk 1')
    chunk2 = monitor.ref_manager.add_chunk('Chunk 2')
    chunk3 = monitor.ref_manager.add_chunk('Chunk 3')
    monitor.ref_manager.add_reference(chunk1, chunk2, ReferenceType.SIMILAR)
    monitor.ref_manager.add_reference(chunk2, chunk3, ReferenceType.SIMILAR)
    monitor.ref_manager.add_reference(chunk3, chunk1, ReferenceType.SIMILAR)
    metrics = monitor.check_reference_health()
    assert metrics.circular_references > 0


def test_health_check_invalid_metadata(monitor):
    """Test health check with invalid reference metadata."""
    chunk1 = monitor.ref_manager.add_chunk('Chunk 1')
    chunk2 = monitor.ref_manager.add_chunk('Chunk 2')
    monitor.ref_manager.add_reference(chunk1, chunk2, ReferenceType.SIMILAR, metadata={'similarity_score': 1.5})
    metrics = monitor.check_reference_health()
    assert metrics.invalid_references > 0


def test_health_check_bidirectional_mismatch(monitor):
    """Test health check with bidirectional reference mismatches."""
    chunk1 = monitor.ref_manager.add_chunk('Chunk 1')
    chunk2 = monitor.ref_manager.add_chunk('Chunk 2')
    monitor.ref_manager.add_reference(chunk1, chunk2, ReferenceType.SIMILAR, bidirectional=True)
    ref = monitor.ref_manager._references[chunk2, chunk1]
    ref.bidirectional = False
    metrics = monitor.check_reference_health()
    assert metrics.bidirectional_mismatches > 0


def test_cache_metrics(monitor):
    """Test cache metrics collection."""
    source_id = next(iter(monitor.ref_manager._chunks.keys()))
    target_id = next(iter(monitor.ref_manager._chunks.values())).id
    monitor.cache.get_reference(source_id, target_id)
    monitor.cache.get_reference(source_id, target_id)
    monitor.cache.get_reference(source_id, target_id)
    metrics = monitor.get_cache_metrics()
    assert metrics is not None
    assert metrics['hit_rate'] == pytest.approx(66.67, rel=0.01, type_validation=True)
    assert metrics['total_requests'] == 3
    assert metrics['hits'] == 2
    assert metrics['misses'] == 1


def test_performance_metrics(monitor):
    """Test performance metrics collection."""

    @time_operation(monitor, 'test_operation')
    def test_operation():
        time.sleep(0.1)
        return True
    for _ in range(3):
        test_operation()
    metrics = monitor.get_performance_metrics()
    assert 'test_operation' in metrics
    assert metrics['test_operation'].operation_count == 3
    assert metrics['test_operation'].avg_time_ms >= 100
    assert metrics['test_operation'].min_time_ms <= metrics['test_operation'].max_time_ms


def test_log_metrics(monitor, caplog):
    """Test metrics logging."""
    with caplog.at_level(logging.INFO):
        monitor.log_metrics()
    assert 'Reference Health Metrics' in caplog.text
    assert 'total=' in caplog.text
    assert 'orphaned=' in caplog.text
    assert 'Cache Metrics' in caplog.text
    assert 'hit_rate=' in caplog.text
    assert 'requests=' in caplog.text
    assert 'Performance Metrics' not in caplog.text


def test_monitor_without_cache():
    """Test monitor functionality without cache component."""
    manager = ReferenceManager()
    monitor = ReferenceMonitor(manager)
    metrics = monitor.check_reference_health()
    assert metrics.total_references == 0
    assert monitor.get_cache_metrics() is None
    monitor.log_metrics()


def test_time_operation_decorator():
    """Test time_operation decorator."""
    manager = ReferenceManager()
    monitor = ReferenceMonitor(manager)

    @time_operation(monitor, 'decorated_operation')
    def decorated_operation(x, y):
        time.sleep(0.01)
        return x + y
    result = decorated_operation(2, 3)
    assert result == 5
    metrics = monitor.get_performance_metrics()
    assert 'decorated_operation' in metrics
    assert metrics['decorated_operation'].operation_count == 1
    assert metrics['decorated_operation'].avg_time_ms >= 10