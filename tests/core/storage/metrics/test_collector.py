"""Tests for storage metrics collector."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from src.core.storage.metrics.collector import MetricsCollector
from src.core.storage.metrics.models import OperationMetrics, PerformanceMetrics, StorageMetrics


@pytest.fixture
def collector(tmp_path: Path) -> MetricsCollector:
    """Create a test metrics collector."""
    storage_path = tmp_path / "storage"
    storage_path.mkdir()
    return MetricsCollector(storage_path, max_history=10, window_seconds=60)


def test_record_operation(collector: MetricsCollector) -> None:
    """Test recording an operation."""
    # Record operation
    collector.record_operation(
        operation_type="create",
        document_id="test123",
        duration_ms=50.5,
        success=True,
    )

    # Get metrics
    metrics = collector.get_performance_metrics()

    # Verify
    assert metrics.avg_latency_ms == 50.5
    assert metrics.throughput_ops > 0
    assert metrics.error_rate == 0.0


def test_record_failed_operation(collector: MetricsCollector) -> None:
    """Test recording a failed operation."""
    # Record failed operation
    collector.record_operation(
        operation_type="create",
        document_id="test123",
        duration_ms=50.5,
        success=False,
        error_message="Test error",
    )

    # Get metrics
    metrics = collector.get_performance_metrics()

    # Verify
    assert metrics.avg_latency_ms == 50.5
    assert metrics.throughput_ops > 0
    assert metrics.error_rate == 1.0


def test_max_history(collector: MetricsCollector) -> None:
    """Test max history limit."""
    # Record more operations than max history
    for i in range(15):
        collector.record_operation(
            operation_type="create",
            document_id=f"test{i}",
            duration_ms=50.0,
            success=True,
        )

    # Get metrics
    metrics = collector.get_performance_metrics()

    # Verify only last 10 operations counted
    assert len(collector._operation_metrics) == 10
    assert metrics.avg_latency_ms == 50.0  # All operations had same duration


def test_performance_metrics_window(collector: MetricsCollector) -> None:
    """Test performance metrics time window."""
    # Record old operation
    collector._operation_metrics.append(
        OperationMetrics(
            operation_type="create",
            document_id="old",
            timestamp=datetime.now(UTC) - timedelta(seconds=120),
            duration_ms=50.0,
            success=True,
        )
    )

    # Record recent operation
    collector.record_operation(
        operation_type="create",
        document_id="recent",
        duration_ms=100.0,
        success=True,
    )

    # Get metrics
    metrics = collector.get_performance_metrics()

    # Verify only recent operation counted
    assert metrics.avg_latency_ms == 100.0


def test_storage_metrics(collector: MetricsCollector) -> None:
    """Test getting storage metrics."""
    # Create some test files
    for i in range(3):
        (collector.storage_path / f"test{i}.json").write_text("{}")

    # Get metrics
    metrics = collector.get_storage_metrics()

    # Verify
    assert isinstance(metrics, StorageMetrics)
    assert metrics.total_documents == 3
    assert metrics.total_space_bytes > 0
    assert metrics.used_space_bytes > 0
    assert metrics.free_space_bytes > 0


def test_clear_metrics(collector: MetricsCollector) -> None:
    """Test clearing metrics."""
    # Record some operations
    for i in range(3):
        collector.record_operation(
            operation_type="create",
            document_id=f"test{i}",
            duration_ms=50.0,
            success=True,
        )

    # Clear metrics
    collector.clear_metrics()

    # Verify
    assert len(collector._operation_metrics) == 0
    metrics = collector.get_performance_metrics()
    assert metrics.avg_latency_ms == 0.0
    assert metrics.throughput_ops == 0.0
    assert metrics.error_rate == 0.0


def test_empty_metrics(collector: MetricsCollector) -> None:
    """Test getting metrics with no operations."""
    metrics = collector.get_performance_metrics()
    assert metrics.avg_latency_ms == 0.0
    assert metrics.throughput_ops == 0.0
    assert metrics.error_rate == 0.0


def test_concurrent_operations(collector: MetricsCollector) -> None:
    """Test concurrent operation recording."""
    import threading

    def record_ops() -> None:
        for i in range(100):
            collector.record_operation(
                operation_type="create",
                document_id=f"test{i}",
                duration_ms=50.0,
                success=True,
            )

    # Start multiple threads
    threads = [threading.Thread(target=record_ops) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Verify
    assert len(collector._operation_metrics) == 10  # max_history limit
    metrics = collector.get_performance_metrics()
    assert metrics.avg_latency_ms == 50.0
