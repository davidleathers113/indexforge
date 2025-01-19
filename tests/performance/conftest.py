from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import pytest


@dataclass
class PerformanceThresholds:
    max_operation_time_ms: int = 1000
    max_batch_operation_time_ms: int = 5000
    max_memory_usage_mb: int = 500
    max_concurrent_operations: int = 50
    max_error_rate_percent: int = 1


@pytest.fixture
def performance_thresholds() -> PerformanceThresholds:
    """Provides performance thresholds for tests."""
    return PerformanceThresholds()


@pytest.fixture
def performance_baseline(tmp_path: Path) -> dict[str, Any]:
    """Loads or creates performance baseline metrics."""
    baseline_file = tmp_path / "performance_baseline.json"
    if baseline_file.exists():
        return json.loads(baseline_file.read_text())
    return {
        "redis": {"single_op_p95_ms": 50, "batch_op_p95_ms": 200, "concurrent_ops_p95_ms": 400},
        "weaviate": {
            "vector_search_p95_ms": 150,
            "batch_index_p95_ms": 300,
            "concurrent_ops_p95_ms": 600,
        },
    }


@pytest.fixture
def performance_metrics_path(tmp_path: Path) -> Path:
    """Provides path for storing performance metrics."""
    metrics_dir = tmp_path / "performance_metrics"
    metrics_dir.mkdir(exist_ok=True)
    return metrics_dir
