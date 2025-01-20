"""Tests for performance instrumentation.

This module contains tests for performance instrumentation functionality.
"""

import logging

import pytest

from src.services.ml.errors import InstrumentationError
from src.services.ml.monitoring.instrumentation import (
    InstrumentationConfig,
    PerformanceInstrumentor,
)
from src.services.ml.monitoring.metrics import MetricsCollector
from src.services.ml.optimization.resources import ResourceManager


@pytest.fixture
def metrics_collector(mocker):
    """Mock metrics collector."""
    collector = mocker.Mock(spec=MetricsCollector)
    return collector


@pytest.fixture
def resource_manager(mocker):
    """Mock resource manager."""
    manager = mocker.Mock(spec=ResourceManager)
    manager.execute_with_resources.side_effect = lambda op, **_: op()
    return manager


@pytest.fixture
def config():
    """Create instrumentation config."""
    return InstrumentationConfig(
        collect_profiles=True,
        track_resources=True,
        log_level=logging.INFO,
        alert_thresholds={
            "duration_ms": 1000.0,
            "memory_mb": 500.0,
            "cpu_percent": 80.0,
        },
    )


@pytest.fixture
def instrumentor(metrics_collector, resource_manager, config):
    """Create performance instrumentor."""
    return PerformanceInstrumentor(metrics_collector, resource_manager, config)


class TestPerformanceInstrumentor:
    """Tests for PerformanceInstrumentor."""

    async def test_instrument_operation_success(self, instrumentor):
        """Test instrumenting successful operation."""

        async def test_op(x: int, y: int) -> int:
            return x + y

        result = await instrumentor.instrument("test_operation", test_op, x=1, y=2)

        assert result == 3
        assert len(instrumentor.get_operation_history()) == 1

    async def test_instrument_operation_error(self, instrumentor):
        """Test instrumenting operation with error."""

        async def error_op():
            raise ValueError("Test error")

        with pytest.raises(InstrumentationError) as exc_info:
            await instrumentor.instrument("error_operation", error_op)

        assert "Failed to instrument error_operation" in str(exc_info.value)
        assert len(instrumentor.get_operation_history()) == 1

    async def test_resource_tracking(self, instrumentor, resource_manager):
        """Test resource tracking during instrumentation."""

        async def test_op():
            return "success"

        await instrumentor.instrument("test_operation", test_op)

        resource_manager.execute_with_resources.assert_called_once()

    async def test_memory_estimation(self, instrumentor):
        """Test memory requirement estimation."""

        async def test_op():
            return "success"

        # Test with different argument types
        args = {
            "list_arg": [1, 2, 3],
            "dict_arg": {"a": 1, "b": 2},
            "str_arg": "test" * 1000,
        }

        await instrumentor.instrument("test_operation", test_op, **args)

        # Memory estimation should account for argument sizes
        history = instrumentor.get_operation_history()
        assert len(history) == 1

    async def test_threshold_alerts(self, instrumentor, mocker):
        """Test performance threshold alerts."""
        # Mock logger
        mock_logger = mocker.patch("src.services.ml.monitoring.instrumentation.logger")

        # Create profile that exceeds thresholds
        profile = mocker.Mock(
            duration_ms=2000.0,  # Exceeds 1000ms threshold
            memory_mb=600.0,  # Exceeds 500MB threshold
            cpu_percent=90.0,  # Exceeds 80% threshold
        )
        instrumentor._profiler.get_active_profiles.return_value = [profile]

        async def test_op():
            return "success"

        await instrumentor.instrument("test_operation", test_op)

        # Verify warnings were logged
        assert mock_logger.warning.call_count == 3

    async def test_clear_history(self, instrumentor):
        """Test clearing operation history."""

        async def test_op():
            return "success"

        await instrumentor.instrument("op1", test_op)
        await instrumentor.instrument("op2", test_op)

        assert len(instrumentor.get_operation_history()) == 2
        instrumentor.clear_history()
        assert len(instrumentor.get_operation_history()) == 0

    async def test_custom_config(self, metrics_collector, resource_manager):
        """Test instrumentor with custom configuration."""
        config = InstrumentationConfig(
            collect_profiles=False,
            track_resources=False,
            log_level=logging.DEBUG,
        )
        instrumentor = PerformanceInstrumentor(metrics_collector, resource_manager, config)

        async def test_op():
            return "success"

        result = await instrumentor.instrument("test_operation", test_op)

        assert result == "success"
        # Resource tracking should be skipped
        resource_manager.execute_with_resources.assert_not_called()
