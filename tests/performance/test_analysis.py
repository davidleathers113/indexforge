"""Tests for performance analysis components."""

from pathlib import Path
from typing import List

import numpy as np
import pytest

from tests.performance.analysis import (
    AnalysisConfig,
    AnalysisConfigFactory,
    AnalysisError,
    AnomalyDetection,
    ChangePointAnalysis,
    MetricsRepository,
    PerformanceAnalysisBuilder,
    PerformanceAnalyzer,
    SeasonalityAnalysis,
)


@pytest.fixture
def sample_metrics() -> List[float]:
    """Generate sample metrics for testing.

    Returns:
        List of sample metric values
    """
    # Generate sinusoidal data with trend and noise
    x = np.linspace(0, 4 * np.pi, 100)
    trend = 0.1 * x
    seasonal = np.sin(x)
    noise = np.random.normal(0, 0.2, 100)
    return list(trend + seasonal + noise)


@pytest.fixture
def temp_metrics_dir(tmp_path: Path) -> Path:
    """Create temporary directory for metrics.

    Args:
        tmp_path: Pytest temporary path fixture

    Returns:
        Path to temporary metrics directory
    """
    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()
    return metrics_dir


def test_seasonality_analysis(sample_metrics):
    """Test seasonality detection."""
    strategy = SeasonalityAnalysis()
    result = strategy.analyze(sample_metrics)

    assert "period" in result
    assert "seasonal_strength" in result
    assert "trend_strength" in result
    assert "has_significant_seasonality" in result
    assert isinstance(result["has_significant_seasonality"], bool)


def test_change_point_analysis(sample_metrics):
    """Test change point detection."""
    strategy = ChangePointAnalysis()
    result = strategy.analyze(sample_metrics, window=5)

    assert "changes" in result
    if result["changes"]:
        change = result["changes"][0]
        assert all(k in change for k in ["index", "p_value", "percent_change", "type"])


def test_anomaly_detection(sample_metrics):
    """Test anomaly detection."""
    # Add some obvious anomalies
    metrics_with_anomalies = sample_metrics.copy()
    metrics_with_anomalies[10] = 100.0  # Large spike
    metrics_with_anomalies[20] = -100.0  # Large dip

    strategy = AnomalyDetection()
    result = strategy.analyze(metrics_with_anomalies)

    assert "z_score" in result
    assert "iqr" in result
    assert "isolation_forest" in result
    assert any(i == 10 for i, _ in result["z_score"])  # Spike detected
    assert any(i == 20 for i, _ in result["z_score"])  # Dip detected


def test_performance_analyzer_integration(sample_metrics):
    """Test full analyzer integration."""
    builder = PerformanceAnalysisBuilder()
    analyzer = (
        builder.add_strategy(SeasonalityAnalysis())
        .add_strategy(ChangePointAnalysis())
        .add_strategy(AnomalyDetection())
        .build()
    )

    results = analyzer.analyze(sample_metrics)
    assert "seasonality" in results
    assert "changepoint" in results
    assert "anomaly" in results


def test_metrics_repository(temp_metrics_dir):
    """Test metrics persistence."""
    repo = MetricsRepository(temp_metrics_dir)
    metrics = {"timestamp": "2024-01-01T00:00:00", "value": 42.0}

    # Test save and load
    repo.save_metrics(metrics, "test_operation")
    loaded = repo.load_metrics("test_operation")
    assert len(loaded) == 1
    assert loaded[0]["value"] == 42.0


def test_analysis_config():
    """Test configuration management."""
    # Test default config
    default_config = AnalysisConfigFactory.create_default_config()
    assert default_config.baseline_threshold == 1.1
    assert len(default_config.metric_paths) > 0

    # Test config serialization
    config_dict = default_config.to_dict()
    restored_config = AnalysisConfig.from_dict(config_dict)
    assert restored_config.baseline_threshold == default_config.baseline_threshold


def test_invalid_inputs():
    """Test error handling for invalid inputs."""
    strategy = SeasonalityAnalysis()

    with pytest.raises(AnalysisError):
        strategy.analyze([])  # Empty input

    with pytest.raises(AnalysisError):
        strategy.analyze([1.0])  # Too few points

    with pytest.raises(AnalysisError):
        strategy.analyze(["not", "numbers"])  # Invalid types


def test_analyzer_error_handling(sample_metrics):
    """Test analyzer error handling."""

    class FailingStrategy(SeasonalityAnalysis):
        def analyze(self, values: List[float], **kwargs):
            raise ValueError("Simulated failure")

    analyzer = PerformanceAnalyzer([FailingStrategy()])
    results = analyzer.analyze(sample_metrics)

    assert "seasonality_error" in results
    assert "Simulated failure" in results["seasonality_error"]
