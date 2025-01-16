"""Base interfaces for metrics collection."""

from abc import ABC, abstractmethod
from typing import Protocol


class MetricCollector(Protocol):
    """Protocol for metric collection."""

    def record_success(self) -> None:
        """Record a successful operation."""
        ...

    def record_error(self, error_type: str = "unknown") -> None:
        """Record an error."""
        ...

    def get_summary(self) -> dict:
        """Get metrics summary."""
        ...


class MetricObserver(Protocol):
    """Protocol for metric observation."""

    def on_metric_update(self, metric_type: str, value: float) -> None:
        """Handle metric update."""
        ...


class BaseMetrics(ABC):
    """Base class for metrics collection."""

    def __init__(self):
        """Initialize metrics."""
        self._observers: list[MetricObserver] = []

    def add_observer(self, observer: MetricObserver) -> None:
        """Add metric observer."""
        self._observers.append(observer)

    def remove_observer(self, observer: MetricObserver) -> None:
        """Remove metric observer."""
        self._observers.remove(observer)

    def notify_observers(self, metric_type: str, value: float) -> None:
        """Notify observers of metric update."""
        for observer in self._observers:
            observer.on_metric_update(metric_type, value)

    @abstractmethod
    def get_summary(self) -> dict:
        """Get metrics summary."""
        pass
