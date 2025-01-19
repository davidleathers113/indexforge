"""Monitoring configuration and metrics collection.

This module provides a centralized interface for application monitoring,
including Prometheus metrics, OpenTelemetry instrumentation, and custom metrics.
"""

from src.api.monitoring.middleware import get_metrics, timing_middleware
from src.api.monitoring.opentelemetry_setup import setup_opentelemetry
from src.api.monitoring.prometheus_metrics import (
    CACHE_HITS,
    CACHE_MISSES,
    CACHE_OPERATION_DURATION,
    DB_OPERATION_DURATION,
    DB_POOL_STATS,
    ERROR_COUNTER,
    EXTERNAL_REQUEST_DURATION,
    EXTERNAL_SERVICE_ERRORS,
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS_TOTAL,
)
from src.api.monitoring.recorders import (
    record_cache_hit,
    record_cache_miss,
    record_cache_operation,
    record_db_operation,
    record_db_pool_stats,
    record_error,
    record_external_request,
)


__all__ = [
    # Middleware
    "timing_middleware",
    "get_metrics",
    # OpenTelemetry
    "setup_opentelemetry",
    # Prometheus Metrics
    "HTTP_REQUEST_DURATION",
    "HTTP_REQUESTS_TOTAL",
    "DB_OPERATION_DURATION",
    "DB_POOL_STATS",
    "CACHE_OPERATION_DURATION",
    "CACHE_HITS",
    "CACHE_MISSES",
    "ERROR_COUNTER",
    "EXTERNAL_REQUEST_DURATION",
    "EXTERNAL_SERVICE_ERRORS",
    # Recorders
    "record_cache_hit",
    "record_cache_miss",
    "record_cache_operation",
    "record_db_operation",
    "record_db_pool_stats",
    "record_error",
    "record_external_request",
]
