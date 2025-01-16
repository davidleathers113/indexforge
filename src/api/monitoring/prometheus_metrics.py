"""Prometheus metrics definitions.

This module defines all Prometheus metrics used throughout the application.
"""

from prometheus_client import Counter, Gauge, Histogram


# HTTP metrics
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency by endpoint",
    ["method", "endpoint", "status_code"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests by endpoint",
    ["method", "endpoint", "status_code"],
)

# Database metrics
DB_OPERATION_DURATION = Histogram(
    "db_operation_duration_seconds",
    "Database operation latency",
    ["operation", "table", "status"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0),
)

DB_POOL_STATS = Gauge(
    "db_pool_stats",
    "Database connection pool statistics",
    ["metric"],
)

# Cache metrics
CACHE_OPERATION_DURATION = Histogram(
    "cache_operation_duration_seconds",
    "Cache operation latency",
    ["operation", "status"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5),
)

CACHE_HITS = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache_type"],
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache_type"],
)

# Error metrics
ERROR_COUNTER = Counter(
    "application_errors_total",
    "Total application errors by type",
    ["error_type", "endpoint", "source"],
)

# External service metrics
EXTERNAL_REQUEST_DURATION = Histogram(
    "external_request_duration_seconds",
    "External service request latency",
    ["service", "operation", "status"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 7.5, 10.0),
)

EXTERNAL_SERVICE_ERRORS = Counter(
    "external_service_errors_total",
    "Total number of external service errors",
    ["service", "operation", "error_type"],
)
