"""Tests for performance profiling.

This module contains tests for operation profiling functionality.
"""

import time

import psutil
import pytest

from src.services.ml.monitoring.metrics import MetricsCollector
from src.services.ml.monitoring.profiler import OperationProfiler, ProfileMetrics


@pytest.fixture
def metrics_collector(mocker):
    """Mock metrics collector."""
    collector = mocker.Mock(spec=MetricsCollector)
    return collector


@pytest.fixture
def mock_process(mocker):
    """Mock psutil Process."""
    process = mocker.Mock(spec=psutil.Process)
    process.cpu_percent.return_value = 50.0
    process.memory_info.return_value.rss = 1024 * 1024 * 100  # 100MB
    process.num_threads.return_value = 4

    ctx_switches = mocker.Mock()
    ctx_switches.voluntary = 100
    ctx_switches.involuntary = 50
    process.num_ctx_switches.return_value = ctx_switches

    io_counters = mocker.Mock()
    io_counters.read_bytes = 1000
    io_counters.write_bytes = 500
    process.io_counters.return_value = io_counters

    return process


@pytest.fixture
def profiler(metrics_collector, mock_process, mocker):
    """Create operation profiler."""
    mocker.patch("psutil.Process", return_value=mock_process)
    return OperationProfiler(metrics_collector)


class TestOperationProfiler:
    """Tests for OperationProfiler."""

    async def test_profile_operation_success(self, profiler, metrics_collector):
        """Test profiling successful operation."""
        with profiler.profile("test_operation"):
            time.sleep(0.1)  # Simulate work

        profiles = profiler.get_active_profiles()
        assert len(profiles) == 1
        profile = profiles[0]

        assert profile.operation_name == "test_operation"
        assert profile.duration_ms >= 100  # At least 100ms
        assert profile.cpu_percent == 50.0
        assert profile.memory_mb == 100.0
        assert profile.thread_count == 4
        assert profile.context_switches == 150

        metrics_collector.record_metric.assert_called_once()

    async def test_profile_operation_error(self, profiler):
        """Test profiling operation with error."""
        with pytest.raises(ValueError):
            with profiler.profile("error_operation"):
                raise ValueError("Test error")

        profiles = profiler.get_active_profiles()
        assert len(profiles) == 1
        profile = profiles[0]

        assert profile.operation_name == "error_operation"
        assert profile.duration_ms > 0

    async def test_multiple_operations(self, profiler):
        """Test profiling multiple operations."""
        with profiler.profile("op1"):
            time.sleep(0.1)

        with profiler.profile("op2"):
            time.sleep(0.1)

        profiles = profiler.get_active_profiles()
        assert len(profiles) == 2
        assert profiles[0].operation_name == "op1"
        assert profiles[1].operation_name == "op2"

    async def test_nested_operations(self, profiler):
        """Test profiling nested operations."""
        with profiler.profile("outer"):
            with profiler.profile("inner"):
                time.sleep(0.1)

        profiles = profiler.get_active_profiles()
        assert len(profiles) == 2
        assert profiles[0].operation_name == "inner"
        assert profiles[1].operation_name == "outer"
        assert profiles[1].duration_ms >= profiles[0].duration_ms

    async def test_clear_profiles(self, profiler):
        """Test clearing profile history."""
        with profiler.profile("test"):
            pass

        assert len(profiler.get_active_profiles()) == 1
        profiler.clear_profiles()
        assert len(profiler.get_active_profiles()) == 0

    async def test_gpu_metrics_collection(self, profiler, mocker):
        """Test GPU metrics collection when available."""
        # Mock torch.cuda
        mock_cuda = mocker.Mock()
        mock_cuda.is_available.return_value = True
        mock_cuda.memory_allocated.return_value = 1024 * 1024 * 500  # 500MB
        mocker.patch.dict("sys.modules", {"torch": mocker.Mock(cuda=mock_cuda)})

        with profiler.profile("gpu_operation"):
            pass

        profile = profiler.get_active_profiles()[0]
        assert profile.gpu_memory_mb == 500.0
