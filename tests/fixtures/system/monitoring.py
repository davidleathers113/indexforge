"""Monitoring fixtures for testing."""

from dataclasses import dataclass, field
import logging
import time
from unittest.mock import MagicMock

import pytest

from ..core.base import BaseState


logger = logging.getLogger(__name__)


@dataclass
class MonitoringState(BaseState):
    """Monitoring state management."""

    metrics: dict[str, float] = field(default_factory=dict)
    labels: dict[str, dict] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    error_mode: bool = False

    def reset(self):
        """Reset state to defaults."""
        super().reset()
        self.metrics.clear()
        self.labels.clear()
        self.start_time = time.time()
        self.error_mode = False

    def record_metric(self, name: str, value: float, labels: dict | None = None):
        """Record a metric value."""
        self.metrics[name] = value
        if labels:
            self.labels[name] = labels


@pytest.fixture(scope="function")
def mock_monitor():
    """Mock monitoring system."""
    mock_mon = MagicMock()
    state = MonitoringState()

    def mock_record(name: str, value: float, labels: dict | None = None):
        """Record a metric."""
        try:
            if state.error_mode:
                state.add_error("Monitoring failed in error mode")
                raise ValueError("Monitoring failed in error mode")

            state.record_metric(name, value, labels)

        except Exception as e:
            state.add_error(str(e))
            raise

    def mock_get_metric(name: str) -> float | None:
        """Get a recorded metric value."""
        return state.metrics.get(name)

    def mock_get_labels(name: str) -> dict | None:
        """Get labels for a metric."""
        return state.labels.get(name)

    # Configure mock methods
    mock_mon.record = MagicMock(side_effect=mock_record)
    mock_mon.get_metric = MagicMock(side_effect=mock_get_metric)
    mock_mon.get_labels = MagicMock(side_effect=mock_get_labels)
    mock_mon.get_errors = state.get_errors
    mock_mon.reset = state.reset
    mock_mon.set_error_mode = lambda enabled=True: setattr(state, "error_mode", enabled)

    yield mock_mon
    state.reset()


@pytest.fixture(scope="function")
def mock_process():
    """Mock process metrics."""
    mock_proc = MagicMock()

    def mock_memory_info():
        return MagicMock(rss=1024 * 1024 * 100)  # 100MB

    def mock_cpu_percent():
        return 5.0  # 5% CPU usage

    # Configure mock methods
    mock_proc.memory_info = MagicMock(side_effect=mock_memory_info)
    mock_proc.cpu_percent = MagicMock(side_effect=mock_cpu_percent)

    return mock_proc


@pytest.fixture(scope="function")
def mock_prometheus():
    """Mock Prometheus metrics."""
    mock_prom = MagicMock()
    state = MonitoringState()

    class MockCounter:
        def inc(self, amount: float = 1):
            try:
                if state.error_mode:
                    state.add_error("Counter increment failed in error mode")
                    raise ValueError("Counter increment failed in error mode")
                current = state.metrics.get(self.name, 0)
                state.record_metric(self.name, current + amount)
            except Exception as e:
                state.add_error(str(e))
                raise

    class MockGauge:
        def set(self, value: float):
            try:
                if state.error_mode:
                    state.add_error("Gauge set failed in error mode")
                    raise ValueError("Gauge set failed in error mode")
                state.record_metric(self.name, value)
            except Exception as e:
                state.add_error(str(e))
                raise

    def mock_counter(name: str, documentation: str, labelnames: list[str] | None = None):
        counter = MockCounter()
        counter.name = name
        return counter

    def mock_gauge(name: str, documentation: str, labelnames: list[str] | None = None):
        gauge = MockGauge()
        gauge.name = name
        return gauge

    # Configure mock methods
    mock_prom.Counter = MagicMock(side_effect=mock_counter)
    mock_prom.Gauge = MagicMock(side_effect=mock_gauge)
    mock_prom.get_metric = lambda name: state.metrics.get(name)
    mock_prom.get_errors = state.get_errors
    mock_prom.reset = state.reset
    mock_prom.set_error_mode = lambda enabled=True: setattr(state, "error_mode", enabled)

    yield mock_prom
    state.reset()
