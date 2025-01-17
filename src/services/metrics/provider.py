"""Metrics provider implementation.

This module provides a concrete implementation of the metrics provider
with support for sampling and async collection.
"""

import random
from threading import Lock
import time

from src.core.interfaces.metrics import MetricsProvider


class SampledMetricsProvider(MetricsProvider):
    """Metrics provider with sampling support."""

    def __init__(self, sample_rate: float = 1.0):
        """Initialize the metrics provider.

        Args:
            sample_rate: Sampling rate between 0 and 1 (default: 1.0)
        """
        self._sample_rate = max(0.0, min(1.0, sample_rate))
        self._counters: dict[str, int] = {}
        self._values: dict[str, list[float]] = {}
        self._timers: dict[str, float] = {}
        self._lock = Lock()

    def _should_sample(self) -> bool:
        """Determine if the current operation should be sampled."""
        return random.random() < self._sample_rate

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric.

        Args:
            name: Name of the counter to increment
            value: Value to increment by (default: 1)
        """
        if not self._should_sample():
            return

        with self._lock:
            if name not in self._counters:
                self._counters[name] = 0
            self._counters[name] += value

    def record_value(self, name: str, value: float) -> None:
        """Record a value metric.

        Args:
            name: Name of the metric
            value: Value to record
        """
        if not self._should_sample():
            return

        with self._lock:
            if name not in self._values:
                self._values[name] = []
            self._values[name].append(value)

    def start_timer(self, name: str) -> None:
        """Start a timer for an operation.

        Args:
            name: Name of the timer
        """
        if not self._should_sample():
            return

        with self._lock:
            self._timers[name] = time.monotonic()

    def stop_timer(self, name: str) -> float | None:
        """Stop a timer and get the elapsed time.

        Args:
            name: Name of the timer to stop

        Returns:
            Optional[float]: Elapsed time in seconds if timer was started
        """
        if name not in self._timers:
            return None

        with self._lock:
            start_time = self._timers.pop(name, None)
            if start_time is not None:
                return time.monotonic() - start_time
            return None

    def get_metrics(self) -> dict[str, dict[str, float]]:
        """Get all collected metrics.

        Returns:
            Dict containing:
                - counters: Dict of counter names to values
                - values: Dict of value names to lists of values
                - timers: Dict of active timer names to start times
        """
        with self._lock:
            metrics = {
                "counters": dict(self._counters),
                "values": {
                    name: {
                        "count": len(values),
                        "mean": sum(values) / len(values) if values else 0,
                        "min": min(values) if values else 0,
                        "max": max(values) if values else 0,
                    }
                    for name, values in self._values.items()
                },
                "active_timers": len(self._timers),
            }
        return metrics

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._values.clear()
            self._timers.clear()
