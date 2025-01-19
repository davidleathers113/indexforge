"""Performance analysis orchestration."""

from datetime import datetime
from typing import Any

from .analyzer import PerformanceAnalyzer
from .config import AnalysisConfig
from .repository import MetricsRepository
from .strategies import (
    AnomalyDetection,
    ChangePointAnalysis,
    CorrelationAnalysis,
    SeasonalityAnalysis,
    TrendAnalysis,
)


class PerformanceAnalysisOrchestrator:
    """Orchestrates the complete performance analysis process."""

    def __init__(
        self,
        metrics_repository: MetricsRepository,
        config: AnalysisConfig,
        analyzer: PerformanceAnalyzer | None = None,
    ):
        """Initialize the orchestrator.

        Args:
            metrics_repository: Repository for loading metrics
            config: Analysis configuration
            analyzer: Optional pre-configured analyzer
        """
        self.repository = metrics_repository
        self.config = config
        self.analyzer = analyzer or self._create_default_analyzer()

    def _create_default_analyzer(self) -> PerformanceAnalyzer:
        """Create default analyzer with all strategies."""
        analyzer = PerformanceAnalyzer()
        analyzer.add_strategy(TrendAnalysis())
        analyzer.add_strategy(SeasonalityAnalysis())
        analyzer.add_strategy(ChangePointAnalysis())
        analyzer.add_strategy(AnomalyDetection())
        analyzer.add_strategy(CorrelationAnalysis())
        return analyzer

    def analyze_operation(self, operation_name: str) -> dict[str, Any]:
        """Analyze performance trends for an operation.

        Args:
            operation_name: Name of the operation to analyze

        Returns:
            Complete analysis results
        """
        # Load metrics
        metrics = self.repository.load_metrics(operation_name)
        if not metrics:
            return {}

        # Initialize analysis result
        analysis = {
            "operation": operation_name,
            "samples": len(metrics),
            "timestamp": datetime.now().isoformat(),
            "trends": {},
            "anomalies": {},
            "regressions": [],
            "correlations": {},
        }

        # Extract metric values
        metric_values = {}
        for path in self.config.metric_paths:
            values = []
            for metric in metrics:
                value = metric
                for key in path:
                    value = value.get(key, {})
                if isinstance(value, (int, float)):
                    values.append(value)
            if values:
                metric_values[".".join(path)] = values

        # Analyze each metric path
        for path in self.config.metric_paths:
            metric_key = ".".join(path)
            if metric_key not in metric_values:
                continue

            values = metric_values[metric_key]

            # Run trend analysis
            trend_results = self.analyzer.analyze(
                values,
                baseline_threshold=self.config.baseline_threshold,
                other_values={k: v for k, v in metric_values.items() if k != metric_key},
            )

            # Store results
            if "trend" in trend_results:
                analysis["trends"][metric_key] = trend_results["trend"]
            if "seasonality" in trend_results:
                if "seasonality" not in analysis:
                    analysis["seasonality"] = {}
                analysis["seasonality"][metric_key] = trend_results["seasonality"]
            if "anomaly" in trend_results:
                analysis["anomalies"][metric_key] = trend_results["anomaly"]
            if "correlation" in trend_results:
                analysis["correlations"][metric_key] = trend_results["correlation"]
            if "changepoint" in trend_results:
                if "change_points" not in analysis:
                    analysis["change_points"] = {}
                analysis["change_points"][metric_key] = trend_results["changepoint"]

            # Check for regressions
            if "trend" in trend_results and trend_results["trend"].get("regression", False):
                analysis["regressions"].append(
                    {
                        "metric": metric_key,
                        "severity": trend_results["trend"]["strength"],
                        "confidence": 1 - trend_results["trend"]["p_value"],
                    }
                )

        return analysis
