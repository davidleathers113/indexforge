"""Performance analysis package.

This package provides tools for analyzing performance metrics using various statistical methods.
It implements the Strategy pattern for different types of analysis, along with supporting
components for configuration management and metrics persistence.
"""

from .analyzer import PerformanceAnalysisBuilder, PerformanceAnalyzer
from .config import AnalysisConfig, AnalysisConfigFactory
from .orchestrator import PerformanceAnalysisOrchestrator
from .repository import MetricsRepository
from .strategies import (
    AnalysisError,
    AnalysisStrategy,
    AnomalyDetection,
    ChangePointAnalysis,
    CorrelationAnalysis,
    SeasonalityAnalysis,
    TrendAnalysis,
)


__all__ = [
    "AnalysisConfig",
    "AnalysisConfigFactory",
    "AnalysisError",
    "AnalysisStrategy",
    "AnomalyDetection",
    "ChangePointAnalysis",
    "CorrelationAnalysis",
    "MetricsRepository",
    "PerformanceAnalysisBuilder",
    "PerformanceAnalysisOrchestrator",
    "PerformanceAnalyzer",
    "SeasonalityAnalysis",
    "TrendAnalysis",
]
