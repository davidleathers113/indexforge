"""Performance settings configuration."""

from typing import Dict

from pydantic import Field, field_validator

from src.api.config.settings import BaseAppSettings


class PerformanceSettings(BaseAppSettings):
    """Performance thresholds and limits settings."""

    PERFORMANCE_THRESHOLDS: Dict[str, float] = Field(
        default={
            "p95_latency_ms": 500.0,  # 95th percentile latency threshold in milliseconds
            "error_rate_threshold": 0.01,  # 1% error rate threshold
            "apdex_threshold": 0.95,  # Apdex score threshold
        },
        description="Performance threshold configurations",
    )

    @field_validator("PERFORMANCE_THRESHOLDS")
    @classmethod
    def validate_performance_thresholds(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate performance thresholds."""
        required_keys = {"p95_latency_ms", "error_rate_threshold", "apdex_threshold"}

        # Check for required keys
        if missing := required_keys - v.keys():
            raise ValueError(f"Missing required threshold keys: {missing}")

        # Validate latency threshold
        if v["p95_latency_ms"] <= 0:
            raise ValueError("p95_latency_ms must be positive")

        # Validate error rate threshold
        if not 0 <= v["error_rate_threshold"] <= 1:
            raise ValueError("error_rate_threshold must be between 0 and 1")

        # Validate Apdex threshold
        if not 0 <= v["apdex_threshold"] <= 1:
            raise ValueError("apdex_threshold must be between 0 and 1")

        return v
