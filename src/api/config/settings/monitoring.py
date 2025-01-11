"""Monitoring and observability settings configuration."""

from typing import Optional

from pydantic import Field, field_validator

from src.api.config.settings import BaseAppSettings


class MonitoringSettings(BaseAppSettings):
    """Monitoring and observability settings."""

    # Sentry Configuration
    SENTRY_DSN: Optional[str] = Field(default=None, description="Sentry Data Source Name")
    SENTRY_TRACES_SAMPLE_RATE: Optional[float] = Field(
        default=None, description="Sample rate for performance monitoring"
    )
    SENTRY_PROFILES_SAMPLE_RATE: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Sample rate for profiling"
    )
    SENTRY_SEND_DEFAULT_PII: bool = Field(
        default=False, description="Include personally identifiable information"
    )
    SENTRY_MAX_BREADCRUMBS: int = Field(
        default=50, ge=0, le=100, description="Maximum number of breadcrumbs"
    )
    SENTRY_ATTACH_STACKTRACE: bool = Field(
        default=True, description="Automatically attach stacktraces"
    )
    SENTRY_REQUEST_BODIES: str = Field(default="small", description="Request body capture size")
    SENTRY_WITH_LOCALS: bool = Field(
        default=True, description="Include local variables in stacktraces"
    )

    # Metrics Configuration
    ENABLE_METRICS: bool = Field(default=True, description="Enable metrics collection")
    METRICS_PORT: int = Field(default=9090, description="Port for metrics server")
    ENABLE_TRACING: bool = Field(default=True, description="Enable distributed tracing")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(
        default="http://jaeger:4317", description="OpenTelemetry collector endpoint"
    )
    OTEL_EXPORTER_OTLP_INSECURE: bool = Field(
        default=True, description="Allow insecure OTLP connection"
    )

    @field_validator("SENTRY_REQUEST_BODIES")
    @classmethod
    def validate_request_bodies(cls, v: str) -> str:
        """Validate request bodies setting."""
        allowed_values = {"never", "small", "always"}
        if v not in allowed_values:
            raise ValueError(f"SENTRY_REQUEST_BODIES must be one of {allowed_values}")
        return v

    @field_validator("SENTRY_TRACES_SAMPLE_RATE")
    @classmethod
    def validate_sample_rate(cls, v: Optional[float]) -> Optional[float]:
        """Validate sample rate is between 0 and 1."""
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError("SENTRY_TRACES_SAMPLE_RATE must be between 0 and 1")
        return v
