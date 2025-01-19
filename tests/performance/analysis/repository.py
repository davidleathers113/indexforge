"""Repository for performance metrics persistence."""

from datetime import datetime
import json
from pathlib import Path
from typing import Any


class MetricsRepository:
    """Repository for storing and retrieving performance metrics."""

    def __init__(self, base_path: Path):
        """Initialize the repository.

        Args:
            base_path: Base path for metrics storage
        """
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def load_metrics(self, operation_name: str) -> list[dict[str, Any]]:
        """Load historical metrics for an operation.

        Args:
            operation_name: Name of the operation

        Returns:
            List of metric dictionaries
        """
        files = sorted(self.base_path.glob(f"{operation_name}_metrics_*.json"))
        metrics = []

        for file in files:
            try:
                metrics.append(json.loads(file.read_text()))
            except json.JSONDecodeError:
                continue

        return metrics

    def save_metrics(self, metrics: dict[str, Any], operation_name: str) -> None:
        """Save metrics for an operation.

        Args:
            metrics: Metrics to save
            operation_name: Name of the operation
        """
        if not metrics:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_file = self.base_path / f"{operation_name}_metrics_{timestamp}.json"
        metrics_file.write_text(json.dumps(metrics, indent=2))

    def save_analysis(self, analysis: dict[str, Any], operation_name: str) -> None:
        """Save analysis results.

        Args:
            analysis: Analysis results to save
            operation_name: Name of the operation
        """
        if not analysis:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_file = self.base_path / f"{operation_name}_analysis_{timestamp}.json"
        analysis_file.write_text(json.dumps(analysis, indent=2))

    def get_latest_metrics(self, operation_name: str) -> dict[str, Any] | None:
        """Get the most recent metrics for an operation.

        Args:
            operation_name: Name of the operation

        Returns:
            Most recent metrics if available
        """
        metrics = self.load_metrics(operation_name)
        return metrics[-1] if metrics else None

    def get_metrics_in_range(
        self, operation_name: str, start_time: datetime, end_time: datetime
    ) -> list[dict[str, Any]]:
        """Get metrics within a time range.

        Args:
            operation_name: Name of the operation
            start_time: Range start time
            end_time: Range end time

        Returns:
            List of metrics within the range
        """
        all_metrics = self.load_metrics(operation_name)

        return [
            metric
            for metric in all_metrics
            if start_time <= datetime.fromisoformat(metric["timestamp"]) <= end_time
        ]
