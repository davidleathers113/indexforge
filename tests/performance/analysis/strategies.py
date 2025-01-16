"""Performance analysis strategies.

This module implements various analysis strategies for performance metrics using the Strategy pattern.
Each strategy focuses on a specific type of analysis while maintaining a consistent interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy import stats
from scipy.signal import find_peaks
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.seasonal import seasonal_decompose


class AnalysisError(Exception):
    """Custom exception for analysis errors."""

    pass


class AnalysisStrategy(ABC):
    """Base class for analysis strategies."""

    @abstractmethod
    def analyze(self, values: List[float], **kwargs) -> Dict[str, Any]:
        """Analyze the given values.

        Args:
            values: List of metric values to analyze
            **kwargs: Additional strategy-specific parameters

        Returns:
            Analysis results

        Raises:
            AnalysisError: If analysis fails or input is invalid
        """
        pass

    def _validate_input(self, values: List[float], min_length: int = 2) -> None:
        """Validate input values.

        Args:
            values: List of values to validate
            min_length: Minimum required length

        Raises:
            AnalysisError: If validation fails
        """
        if not values:
            raise AnalysisError("No values provided for analysis")
        if len(values) < min_length:
            raise AnalysisError(f"Insufficient data points. Need at least {min_length}")
        if not all(isinstance(v, (int, float)) for v in values):
            raise AnalysisError("All values must be numeric")


class SeasonalityAnalysis(AnalysisStrategy):
    """Detect and analyze seasonality in time series data."""

    def analyze(self, values: List[float], period: Optional[int] = None) -> Dict[str, Any]:
        """Analyze seasonality patterns.

        Args:
            values: List of metric values
            period: Optional period for decomposition

        Returns:
            Seasonality analysis results including period, strengths, and significance

        Raises:
            AnalysisError: If analysis fails or input is invalid
        """
        try:
            self._validate_input(values, min_length=4)
            ts = np.array(values)

            if period is None:
                acf = np.correlate(ts - np.mean(ts), ts - np.mean(ts), mode="full")
                peaks, _ = find_peaks(acf[len(acf) // 2 :], distance=1)
                period = peaks[0] if len(peaks) > 0 else len(ts) // 4

            decomposition = seasonal_decompose(
                ts, period=min(period, len(ts) // 2), extrapolate_trend="freq"
            )

            return {
                "period": period,
                "seasonal_strength": float(np.std(decomposition.seasonal) / np.std(ts)),
                "trend_strength": float(np.std(decomposition.trend) / np.std(ts)),
                "residual_strength": float(np.std(decomposition.resid) / np.std(ts)),
                "has_significant_seasonality": bool(
                    np.std(decomposition.seasonal) > 0.1 * np.std(ts)
                ),
            }
        except (ValueError, np.linalg.LinAlgError, NotImplementedError) as e:
            raise AnalysisError(f"Seasonality analysis failed: {str(e)}")


class ChangePointAnalysis(AnalysisStrategy):
    """Detect significant changes in metric behavior."""

    def analyze(self, values: List[float], window: int = 10) -> Dict[str, Any]:
        """Detect change points in the time series.

        Args:
            values: List of metric values
            window: Window size for detection (must be >= 2)

        Returns:
            Detected change points with metadata including significance and type

        Raises:
            AnalysisError: If analysis fails or input is invalid
        """
        try:
            self._validate_input(values, min_length=window * 2)
            if window < 2:
                raise AnalysisError("Window size must be at least 2")

            ts = np.array(values)
            changes = []

            for i in range(window, len(ts) - window):
                before = ts[i - window : i]
                after = ts[i : i + window]

                t_stat, p_value = stats.ttest_ind(before, after)

                if p_value < 0.05:
                    percent_change = float(
                        ((np.mean(after) - np.mean(before)) / np.mean(before)) * 100
                    )
                    changes.append(
                        {
                            "index": i,
                            "timestamp": i,
                            "p_value": float(p_value),
                            "percent_change": percent_change,
                            "type": "increase" if percent_change > 0 else "decrease",
                            "significance": float(-np.log10(p_value)),
                        }
                    )

            return {"changes": changes}
        except Exception as e:
            raise AnalysisError(f"Change point analysis failed: {str(e)}")


class AnomalyDetection(AnalysisStrategy):
    """Detect anomalies using multiple methods."""

    def analyze(self, values: List[float], contamination: float = 0.1) -> Dict[str, Any]:
        """Detect anomalies in the metric values.

        Args:
            values: List of metric values
            contamination: Expected proportion of outliers (0 < contamination < 0.5)

        Returns:
            Anomalies detected by different methods (z-score, IQR, isolation forest)

        Raises:
            AnalysisError: If analysis fails or input is invalid
        """
        try:
            self._validate_input(values, min_length=10)
            if not 0 < contamination < 0.5:
                raise AnalysisError("Contamination must be between 0 and 0.5")

            results: Dict[str, List[Tuple[int, float]]] = {}
            ts = np.array(values)

            # Z-score method
            mean = np.mean(ts)
            std = np.std(ts)
            z_scores = [(i, float((x - mean) / std)) for i, x in enumerate(ts)]
            results["z_score"] = [(i, z) for i, z in z_scores if abs(z) > 2.0]

            # IQR method
            q1 = float(np.percentile(ts, 25))
            q3 = float(np.percentile(ts, 75))
            iqr = q3 - q1
            results["iqr"] = [
                (i, float(x))
                for i, x in enumerate(ts)
                if x < (q1 - 1.5 * iqr) or x > (q3 + 1.5 * iqr)
            ]

            # Isolation Forest
            clf = IsolationForest(random_state=42, contamination=contamination)
            predictions = clf.fit_predict(ts.reshape(-1, 1))
            results["isolation_forest"] = [
                (i, float(ts[i])) for i, pred in enumerate(predictions) if pred == -1
            ]

            return results
        except Exception as e:
            raise AnalysisError(f"Anomaly detection failed: {str(e)}")


class TrendAnalysis(AnalysisStrategy):
    """Analyze trends and correlations in metric data."""

    def analyze(self, values: List[float], baseline_threshold: float = 1.1) -> Dict[str, Any]:
        """Calculate comprehensive trend statistics.

        Args:
            values: List of metric values
            baseline_threshold: Threshold for regression detection (e.g., 1.1 = 10% increase)

        Returns:
            Trend analysis results including slope, significance, and stability

        Raises:
            AnalysisError: If analysis fails or input is invalid
        """
        try:
            self._validate_input(values, min_length=2)
            ts = np.array(values)
            x = np.arange(len(ts))

            # Basic trend analysis
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, ts)

            trend_analysis = {
                "slope": float(slope),
                "r_squared": float(r_value**2),
                "p_value": float(p_value),
                "std_err": float(std_err),
                "trend_direction": "increasing" if slope > 0 else "decreasing",
                "significant": bool(p_value < 0.05),
                "strength": float(abs(r_value)),
                "stability": float(1 - std_err / abs(slope) if slope != 0 else 0),
            }

            # Detect regression
            if slope > 0 and trend_analysis["significant"]:
                predicted_increase = (slope * len(ts)) / ts[0] if ts[0] != 0 else float("inf")
                trend_analysis["regression"] = bool(predicted_increase > baseline_threshold)

            return trend_analysis
        except Exception as e:
            raise AnalysisError(f"Trend analysis failed: {str(e)}")


class CorrelationAnalysis(AnalysisStrategy):
    """Analyze correlations between multiple metrics."""

    def analyze(self, values: List[float], other_values: Dict[str, List[float]]) -> Dict[str, Any]:
        """Calculate correlations between metrics.

        Args:
            values: Primary metric values
            other_values: Dictionary of other metric names and their values

        Returns:
            Correlation analysis results

        Raises:
            AnalysisError: If analysis fails or input is invalid
        """
        try:
            self._validate_input(values, min_length=2)
            results = {}

            for metric_name, other_metric in other_values.items():
                if len(other_metric) != len(values):
                    continue

                correlation, p_value = stats.pearsonr(values, other_metric)
                results[metric_name] = {
                    "correlation": float(correlation),
                    "p_value": float(p_value),
                    "significant": bool(p_value < 0.05),
                    "strength": (
                        "strong"
                        if abs(correlation) > 0.7
                        else "moderate" if abs(correlation) > 0.3 else "weak"
                    ),
                }

            return results
        except Exception as e:
            raise AnalysisError(f"Correlation analysis failed: {str(e)}")
