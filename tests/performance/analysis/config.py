"""Configuration factory for performance analysis."""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Union

import numpy as np


@dataclass
class AnalysisConfig:
    """Configuration settings for performance analysis."""

    metric_paths: List[List[str]]
    baseline_threshold: float
    correlation_threshold: float
    significance_level: float
    seasonality_min_periods: int
    change_point_window: int
    anomaly_contamination: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary.

        Returns:
            Dictionary representation of config
        """
        return {
            "metric_paths": self.metric_paths,
            "baseline_threshold": float(self.baseline_threshold),
            "correlation_threshold": float(self.correlation_threshold),
            "significance_level": float(self.significance_level),
            "seasonality_min_periods": int(self.seasonality_min_periods),
            "change_point_window": int(self.change_point_window),
            "anomaly_contamination": float(self.anomaly_contamination),
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "AnalysisConfig":
        """Create config from dictionary.

        Args:
            config_dict: Dictionary of configuration values

        Returns:
            Config instance
        """
        return cls(
            metric_paths=config_dict["metric_paths"],
            baseline_threshold=float(config_dict["baseline_threshold"]),
            correlation_threshold=float(config_dict["correlation_threshold"]),
            significance_level=float(config_dict["significance_level"]),
            seasonality_min_periods=int(config_dict["seasonality_min_periods"]),
            change_point_window=int(config_dict["change_point_window"]),
            anomaly_contamination=float(config_dict["anomaly_contamination"]),
        )


class AnalysisConfigFactory:
    """Factory for creating analysis configurations."""

    @staticmethod
    def create_default_config() -> AnalysisConfig:
        """Create default analysis configuration.

        Returns:
            Default configuration instance
        """
        return AnalysisConfig(
            metric_paths=[
                ["duration_ms", "p95"],
                ["memory_mb", "max"],
                ["cpu_percent", "mean"],
                ["error_count", "sum"],
            ],
            baseline_threshold=1.1,  # 10% deviation threshold
            correlation_threshold=0.5,  # Medium correlation strength
            significance_level=0.05,  # 95% confidence level
            seasonality_min_periods=4,
            change_point_window=10,
            anomaly_contamination=0.1,  # Expected 10% anomalies
        )

    @staticmethod
    def create_sensitive_config() -> AnalysisConfig:
        """Create configuration with higher sensitivity.

        Returns:
            Sensitive configuration instance
        """
        return AnalysisConfig(
            metric_paths=[
                ["duration_ms", "p95"],
                ["duration_ms", "p99"],
                ["memory_mb", "max"],
                ["memory_mb", "p95"],
                ["cpu_percent", "mean"],
                ["cpu_percent", "max"],
                ["error_count", "sum"],
                ["error_rate", "mean"],
            ],
            baseline_threshold=1.05,  # 5% deviation threshold
            correlation_threshold=0.3,  # Lower correlation threshold
            significance_level=0.01,  # 99% confidence level
            seasonality_min_periods=3,
            change_point_window=5,
            anomaly_contamination=0.05,  # Expected 5% anomalies
        )

    @staticmethod
    def create_robust_config() -> AnalysisConfig:
        """Create configuration that's more resistant to noise.

        Returns:
            Robust configuration instance
        """
        return AnalysisConfig(
            metric_paths=[
                ["duration_ms", "median"],
                ["memory_mb", "median"],
                ["cpu_percent", "median"],
                ["error_count", "sum"],
            ],
            baseline_threshold=1.2,  # 20% deviation threshold
            correlation_threshold=0.7,  # Strong correlation threshold
            significance_level=0.001,  # 99.9% confidence level
            seasonality_min_periods=6,
            change_point_window=20,
            anomaly_contamination=0.01,  # Expected 1% anomalies
        )
