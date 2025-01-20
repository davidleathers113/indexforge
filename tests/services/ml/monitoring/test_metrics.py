"""Tests for metrics collection functionality.

This module contains tests for the metrics collection system, covering:
1. Basic metric recording and retrieval
2. Metric aggregation and statistics
3. Resource usage tracking
4. Error rate monitoring
5. Batch operation metrics
"""

import logging
from typing import Dict, List
from unittest.mock import Mock, patch

import pytest

from src.services.ml.monitoring.metrics import MetricsCollector, OperationMetrics, ResourceMetrics


@pytest.fixture
def metrics_collector():
    """Create metrics collector with mocked storage."""
    return MetricsCollector()


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    async def test_record_basic_metric(self, metrics_collector):
        """Test recording a basic operation metric."""
        await metrics_collector.record_metric(
            name="test_operation",
            duration_ms=100.0,
            memory_mb=50.0,
            metadata={"batch_size": 10},
        )

        metrics = metrics_collector.get_metrics("test_operation")
        assert len(metrics) == 1
        assert metrics[0].duration_ms == 100.0
        assert metrics[0].memory_mb == 50.0
        assert metrics[0].metadata["batch_size"] == 10

    async def test_record_multiple_metrics(self, metrics_collector):
        """Test recording and aggregating multiple metrics."""
        operations = [
            ("op1", 100.0, 50.0),
            ("op1", 150.0, 60.0),
            ("op2", 200.0, 70.0),
        ]

        for name, duration, memory in operations:
            await metrics_collector.record_metric(
                name=name,
                duration_ms=duration,
                memory_mb=memory,
            )

        # Check op1 metrics
        op1_metrics = metrics_collector.get_metrics("op1")
        assert len(op1_metrics) == 2
        assert sum(m.duration_ms for m in op1_metrics) == 250.0

        # Check op2 metrics
        op2_metrics = metrics_collector.get_metrics("op2")
        assert len(op2_metrics) == 1
        assert op2_metrics[0].duration_ms == 200.0

    async def test_resource_metrics_tracking(self, metrics_collector):
        """Test tracking resource usage metrics."""
        with patch("psutil.Process") as mock_process:
            # Mock process metrics
            mock_process.return_value.memory_info.return_value.rss = 1024 * 1024 * 100  # 100MB
            mock_process.return_value.cpu_percent.return_value = 50.0

            await metrics_collector.record_resource_metrics(
                operation_name="resource_test",
                resource_metrics=ResourceMetrics(
                    memory_mb=100.0,
                    cpu_percent=50.0,
                    gpu_memory_mb=None,
                    thread_count=4,
                ),
            )

            metrics = metrics_collector.get_resource_metrics("resource_test")
            assert len(metrics) == 1
            assert metrics[0].memory_mb == 100.0
            assert metrics[0].cpu_percent == 50.0
            assert metrics[0].thread_count == 4

    async def test_batch_operation_metrics(self, metrics_collector):
        """Test recording metrics for batch operations."""
        batch_sizes = [5, 10, 15]

        for size in batch_sizes:
            await metrics_collector.record_metric(
                name="batch_operation",
                duration_ms=size * 10.0,  # Simulated duration
                memory_mb=size * 5.0,  # Simulated memory usage
                metadata={
                    "batch_size": size,
                    "success_count": size - 1,
                    "error_count": 1,
                },
            )

        metrics = metrics_collector.get_metrics("batch_operation")
        assert len(metrics) == 3

        # Verify batch size correlation with resource usage
        for i, metric in enumerate(metrics):
            assert metric.metadata["batch_size"] == batch_sizes[i]
            assert metric.duration_ms == batch_sizes[i] * 10.0
            assert metric.memory_mb == batch_sizes[i] * 5.0

    async def test_error_rate_tracking(self, metrics_collector):
        """Test tracking operation error rates."""
        # Record mix of successful and failed operations
        operations = [
            ("success", None),
            ("error", ValueError("test error")),
            ("success", None),
            ("success", None),
            ("error", RuntimeError("another error")),
        ]

        for status, error in operations:
            await metrics_collector.record_metric(
                name="error_test",
                duration_ms=100.0,
                memory_mb=50.0,
                metadata={
                    "status": status,
                    "error": str(error) if error else None,
                },
            )

        metrics = metrics_collector.get_metrics("error_test")
        error_count = sum(1 for m in metrics if m.metadata["status"] == "error")
        success_count = sum(1 for m in metrics if m.metadata["status"] == "success")

        assert len(metrics) == 5
        assert error_count == 2
        assert success_count == 3

    async def test_metric_aggregation(self, metrics_collector):
        """Test metric aggregation and statistics."""
        # Record metrics with varying values
        durations = [100.0, 150.0, 200.0, 250.0]
        memory_usage = [50.0, 60.0, 70.0, 80.0]

        for duration, memory in zip(durations, memory_usage):
            await metrics_collector.record_metric(
                name="aggregate_test",
                duration_ms=duration,
                memory_mb=memory,
            )

        stats = metrics_collector.get_operation_stats("aggregate_test")

        # Verify duration statistics
        assert stats["duration_ms"]["avg"] == sum(durations) / len(durations)
        assert stats["duration_ms"]["min"] == min(durations)
        assert stats["duration_ms"]["max"] == max(durations)

        # Verify memory statistics
        assert stats["memory_mb"]["avg"] == sum(memory_usage) / len(memory_usage)
        assert stats["memory_mb"]["min"] == min(memory_usage)
        assert stats["memory_mb"]["max"] == max(memory_usage)

    def test_clear_metrics(self, metrics_collector):
        """Test clearing metrics for specific operations."""
        # Record metrics for different operations
        operations = ["op1", "op2", "op3"]
        for op in operations:
            metrics_collector.record_metric(
                name=op,
                duration_ms=100.0,
                memory_mb=50.0,
            )

        # Clear metrics for op1
        metrics_collector.clear_metrics("op1")
        assert len(metrics_collector.get_metrics("op1")) == 0
        assert len(metrics_collector.get_metrics("op2")) == 1
        assert len(metrics_collector.get_metrics("op3")) == 1

        # Clear all metrics
        metrics_collector.clear_all_metrics()
        for op in operations:
            assert len(metrics_collector.get_metrics(op)) == 0
