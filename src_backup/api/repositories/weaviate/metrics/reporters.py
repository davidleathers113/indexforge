"""Metric reporting functionality."""

from abc import ABC, abstractmethod

from .base import MetricObserver


class MetricReportBuilder(ABC):
    """Abstract base class for metric report builders."""

    @abstractmethod
    def add_batch_metrics(self, metrics: dict) -> None:
        """Add batch metrics to report."""
        pass

    @abstractmethod
    def add_performance_metrics(self, metrics: dict) -> None:
        """Add performance metrics to report."""
        pass

    @abstractmethod
    def build(self) -> dict:
        """Build the final report."""
        pass


class DetailedReportBuilder(MetricReportBuilder):
    """Builds detailed metric reports."""

    def __init__(self):
        """Initialize report builder."""
        self.batch_metrics: dict = {}
        self.performance_metrics: dict = {}

    def add_batch_metrics(self, metrics: dict) -> None:
        """Add batch metrics to report."""
        self.batch_metrics = metrics

    def add_performance_metrics(self, metrics: dict) -> None:
        """Add performance metrics to report."""
        self.performance_metrics = metrics

    def build(self) -> dict:
        """Build detailed report."""
        return {
            "batch_operations": self.batch_metrics,
            "performance": self.performance_metrics,
            "summary": self._build_summary(),
        }

    def _build_summary(self) -> dict:
        """Build summary section of report."""
        return {
            "total_operations": self.batch_metrics.get("batches", {}).get("total", 0),
            "success_rate": self.batch_metrics.get("batches", {}).get("success_rate", 0),
            "avg_throughput": self.performance_metrics.get("throughput", {}).get("mean", 0),
            "optimal_batch_size": self.performance_metrics.get("optimal_batch_size", 0),
        }


class MetricReporter(MetricObserver):
    """Reports and aggregates metrics."""

    def __init__(self, report_builder: MetricReportBuilder):
        """Initialize reporter with builder."""
        self.builder = report_builder
        self.metric_updates: list[dict] = []

    def on_metric_update(self, metric_type: str, value: float) -> None:
        """Handle metric update."""
        self.metric_updates.append({"type": metric_type, "value": value})

    def generate_report(self, batch_metrics: dict, performance_metrics: dict) -> dict:
        """Generate metric report.

        Args:
            batch_metrics: Current batch metrics
            performance_metrics: Current performance metrics

        Returns:
            Complete metric report
        """
        self.builder.add_batch_metrics(batch_metrics)
        self.builder.add_performance_metrics(performance_metrics)
        return self.builder.build()
