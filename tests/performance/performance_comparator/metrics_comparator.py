"""Module for comparing performance metrics between versions."""

from typing import Dict, List, Tuple

import pandas as pd
from loguru import logger

# Define metric mappings for import and search operations
IMPORT_METRICS: List[Tuple[str, str]] = [
    ("duration_seconds", "Import Duration (s)"),
    ("docs_per_second", "Documents/Second"),
    ("failed_imports", "Failed Imports"),
]

SEARCH_METRICS: List[Tuple[str, str]] = [
    ("duration_seconds", "Search Duration (s)"),
    ("queries_per_second", "Queries/Second"),
    ("avg_query_time", "Avg Query Time (s)"),
    ("failed_queries", "Failed Queries"),
]


def calculate_metric_change(v3_value: float, v4_value: float) -> Tuple[float, float]:
    """Calculate the difference and percentage change between two metric values.

    Args:
        v3_value: Value from v3
        v4_value: Value from v4

    Returns:
        Tuple of (difference, percent_change)
    """
    difference = v4_value - v3_value
    percent_change = (difference / max(abs(v3_value), 1)) * 100
    return difference, percent_change


def compare_import_metrics(v3_results: Dict, v4_results: Dict) -> List[Dict]:
    """Compare import metrics between versions.

    Args:
        v3_results: Results from v3 tests
        v4_results: Results from v4 tests

    Returns:
        List of metric comparison dictionaries
    """
    metrics = []
    v3_import = v3_results.get("import_metrics", {})
    v4_import = v4_results.get("import_metrics", {})

    for key, label in IMPORT_METRICS:
        v3_value = v3_import.get(key, 0)
        v4_value = v4_import.get(key, 0)
        difference, percent_change = calculate_metric_change(v3_value, v4_value)

        metrics.append(
            {
                "metric": label,
                "v3": v3_value,
                "v4": v4_value,
                "difference": difference,
                "percent_change": percent_change,
            }
        )

    return metrics


def compare_search_metrics(v3_results: Dict, v4_results: Dict) -> List[Dict]:
    """Compare search metrics between versions.

    Args:
        v3_results: Results from v3 tests
        v4_results: Results from v4 tests

    Returns:
        List of metric comparison dictionaries
    """
    metrics = []
    v3_search = v3_results.get("search_metrics", {})
    v4_search = v4_results.get("search_metrics", {})

    for key, label in SEARCH_METRICS:
        v3_value = v3_search.get(key, 0)
        v4_value = v4_search.get(key, 0)
        difference, percent_change = calculate_metric_change(v3_value, v4_value)

        metrics.append(
            {
                "metric": label,
                "v3": v3_value,
                "v4": v4_value,
                "difference": difference,
                "percent_change": percent_change,
            }
        )

    return metrics


def compare_metrics(v3_results: Dict, v4_results: Dict) -> pd.DataFrame:
    """Compare all metrics between versions.

    Args:
        v3_results: Results from v3 tests
        v4_results: Results from v4 tests

    Returns:
        DataFrame containing metric comparisons
    """
    try:
        metrics = []
        metrics.extend(compare_import_metrics(v3_results, v4_results))
        metrics.extend(compare_search_metrics(v3_results, v4_results))

        return pd.DataFrame(metrics)

    except Exception as e:
        logger.error(f"Error comparing metrics: {e}")
        raise
