"""Tests for storage metrics collection."""

from pathlib import Path
import time

import pytest

from src.core.models.settings import Settings
from src.core.tracking.metrics import StorageMetricsCollector


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Provide test settings."""
    return Settings(
        storage_path=tmp_path / "test_storage", max_metrics_history=5, metrics_enabled=True
    )


@pytest.fixture
def metrics(settings: Settings) -> StorageMetricsCollector:
    """Provide metrics collector instance."""
    return StorageMetricsCollector(settings)


def test_record_operation(metrics: StorageMetricsCollector):
    """Test recording operation metrics."""
    metrics.record_operation("test_op", 1.5)
    assert metrics.get_metrics()["test_op"] == [1.5]


def test_max_history_limit(metrics: StorageMetricsCollector):
    """Test max history limit is enforced."""
    for i in range(10):
        metrics.record_operation("test_op", float(i))

    # Should only keep last 5 entries due to max_metrics_history setting
    assert len(metrics.get_metrics()["test_op"]) == 5
    assert metrics.get_metrics()["test_op"] == [5.0, 6.0, 7.0, 8.0, 9.0]


def test_operation_timing(metrics: StorageMetricsCollector):
    """Test operation timing functionality."""
    metrics.start_operation("test_op")
    time.sleep(0.1)  # Simulate work
    metrics.end_operation("test_op")

    durations = metrics.get_metrics()["test_op"]
    assert len(durations) == 1
    assert 0.1 <= durations[0] <= 0.2  # Allow for some timing variance


def test_end_operation_without_start(metrics: StorageMetricsCollector):
    """Test ending operation that wasn't started raises error."""
    with pytest.raises(ValueError):
        metrics.end_operation("nonexistent_op")


def test_get_average_duration(metrics: StorageMetricsCollector):
    """Test average duration calculation."""
    durations = [1.0, 2.0, 3.0]
    for duration in durations:
        metrics.record_operation("test_op", duration)

    assert metrics.get_average_duration("test_op") == 2.0
    assert metrics.get_average_duration("nonexistent_op") == 0.0


def test_clear_metrics(metrics: StorageMetricsCollector):
    """Test clearing metrics."""
    metrics.record_operation("test_op", 1.0)
    metrics.start_operation("ongoing_op")

    metrics.clear_metrics()
    assert not metrics.get_metrics()

    # Should be able to end operation after clear
    with pytest.raises(ValueError):
        metrics.end_operation("ongoing_op")


def test_multiple_operations(metrics: StorageMetricsCollector):
    """Test handling multiple operations."""
    metrics.record_operation("op1", 1.0)
    metrics.record_operation("op2", 2.0)

    all_metrics = metrics.get_metrics()
    assert len(all_metrics) == 2
    assert all_metrics["op1"] == [1.0]
    assert all_metrics["op2"] == [2.0]


def test_operation_names_preserved(metrics: StorageMetricsCollector):
    """Test operation names are preserved exactly."""
    test_ops = ["Create", "UPDATE", "delete_item", "Get.Value"]
    for op in test_ops:
        metrics.record_operation(op, 1.0)

    recorded_ops = metrics.get_metrics().keys()
    assert all(op in recorded_ops for op in test_ops)
