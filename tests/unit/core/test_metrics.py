"""Unit tests for metrics collection system."""

import asyncio
from datetime import datetime, timedelta

import pytest

from src.core.metrics import OperationMetrics, ServiceMetricsCollector


class TestServiceMetricsCollector:
    """Test metrics collection functionality."""

    @pytest.fixture
    def metrics_collector(self) -> ServiceMetricsCollector:
        """Create metrics collector for testing."""
        return ServiceMetricsCollector(
            service_name="test_service",
            max_history=100,
            memory_threshold_mb=500,
        )

    def test_basic_operation_tracking(self, metrics_collector: ServiceMetricsCollector):
        """Test basic operation metrics collection."""
        with metrics_collector.measure_operation("test_op"):
            # Simulate work
            for _ in range(1000000):
                pass

        metrics = metrics_collector.get_current_metrics()
        assert metrics["service_name"] == "test_service"
        assert metrics["total_operations"] == 1
        assert metrics["error_rate"] == 0
        assert metrics["avg_duration"] > 0
        assert metrics["max_memory_mb"] > 0

    def test_operation_with_metadata(self, metrics_collector: ServiceMetricsCollector):
        """Test operation tracking with metadata."""
        test_metadata = {"key": "value", "count": 42}

        with metrics_collector.measure_operation("test_op", test_metadata):
            pass

        assert len(metrics_collector.operations) == 1
        assert metrics_collector.operations[0].metadata == test_metadata

    def test_error_tracking(self, metrics_collector: ServiceMetricsCollector):
        """Test error tracking in operations."""
        # Successful operation
        with metrics_collector.measure_operation("success_op"):
            pass

        # Failed operation
        with pytest.raises(ValueError):
            with metrics_collector.measure_operation("error_op"):
                raise ValueError("Test error")

        metrics = metrics_collector.get_current_metrics()
        assert metrics["error_rate"] == 0.5  # 1 error out of 2 operations
        assert metrics["error_counts"]["error_op"] == 1
        assert metrics["error_counts"].get("success_op", 0) == 0

    def test_memory_tracking(self, metrics_collector: ServiceMetricsCollector):
        """Test memory usage tracking."""
        # Operation with significant memory usage
        with metrics_collector.measure_operation("memory_op"):
            large_list = [0] * 1000000  # Allocate memory
            _ = len(large_list)  # Use the list to prevent optimization

        metrics = metrics_collector.get_current_metrics()
        assert metrics["max_memory_mb"] > 0
        assert metrics["avg_memory_mb"] > 0

    def test_operation_timing(self, metrics_collector: ServiceMetricsCollector):
        """Test operation timing accuracy."""
        sleep_duration = 0.1

        with metrics_collector.measure_operation("timing_op"):
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(sleep_duration))

        metrics = metrics_collector.get_current_metrics()
        assert metrics["avg_duration"] >= sleep_duration
        assert metrics["max_duration"] >= sleep_duration

    def test_max_history_limit(self, metrics_collector: ServiceMetricsCollector):
        """Test max history limit enforcement."""
        max_ops = metrics_collector.max_history

        # Generate more operations than max_history
        for i in range(max_ops + 10):
            with metrics_collector.measure_operation(f"op_{i}"):
                pass

        assert len(metrics_collector.operations) == max_ops
        # Verify we have the most recent operations
        assert metrics_collector.operations[-1].operation_name == f"op_{max_ops + 9}"

    def test_health_check(self, metrics_collector: ServiceMetricsCollector):
        """Test health check functionality."""
        # Generate some healthy operations
        for _ in range(5):
            with metrics_collector.measure_operation("healthy_op"):
                pass

        # Generate some errors
        for _ in range(2):
            with pytest.raises(ValueError):
                with metrics_collector.measure_operation("error_op"):
                    raise ValueError("Test error")

        health = metrics_collector.check_health()
        assert "status" in health
        assert "checks" in health
        assert "memory_usage" in health["checks"]
        assert "error_rate" in health["checks"]
        assert "performance" in health["checks"]

    def test_operation_filtering(self, metrics_collector: ServiceMetricsCollector):
        """Test operation metrics filtering by time window."""
        # Generate operations at different times
        for i in range(3):
            op = OperationMetrics(
                operation_name="test_op",
                start_time=datetime.now() - timedelta(minutes=i),
            )
            op.end_time = op.start_time + timedelta(seconds=1)
            op.duration = 1.0
            metrics_collector.operations.append(op)

        # Get metrics for last minute
        metrics = metrics_collector.get_operation_metrics(
            "test_op",
            time_window=timedelta(minutes=1),
        )
        assert metrics["total_calls"] == 3  # All operations counted
        assert "avg_duration" in metrics
        assert "success_rate" in metrics

    def test_slow_operation_tracking(self, metrics_collector: ServiceMetricsCollector):
        """Test tracking of slow operations."""
        # Fast operation
        with metrics_collector.measure_operation("fast_op"):
            pass

        # Slow operation
        with metrics_collector.measure_operation("slow_op"):
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.2))

        metrics = metrics_collector.get_current_metrics()
        assert "slow_op" in metrics["slow_operations"]
        assert "fast_op" not in metrics["slow_operations"]

    def test_reset_functionality(self, metrics_collector: ServiceMetricsCollector):
        """Test metrics reset functionality."""
        # Generate some operations
        with metrics_collector.measure_operation("test_op"):
            pass

        with pytest.raises(ValueError):
            with metrics_collector.measure_operation("error_op"):
                raise ValueError("Test error")

        # Verify metrics exist
        assert metrics_collector.operations
        assert metrics_collector.error_counts
        assert metrics_collector.operation_counts

        # Reset metrics
        metrics_collector.reset()

        # Verify everything is cleared
        assert not metrics_collector.operations
        assert not metrics_collector.error_counts
        assert not metrics_collector.operation_counts
        assert not metrics_collector.slow_operations
        assert metrics_collector._current_operation is None
