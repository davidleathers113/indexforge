"""Monitoring configuration and metrics collection.

This module provides centralized configuration for application monitoring,
including Prometheus metrics, OpenTelemetry instrumentation, and custom metrics.
"""

import time
from typing import Callable

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio
from prometheus_client import REGISTRY, Counter, Gauge, Histogram
from prometheus_client.openmetrics.exposition import generate_latest

from src.api.config.settings import settings

# Initialize optional OpenTelemetry components
HAS_OTEL_INSTRUMENTATION = False
OTLPSpanExporter = None
FastAPIInstrumentor = None
RequestsInstrumentor = None
SQLAlchemyInstrumentor = None

try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    HAS_OTEL_INSTRUMENTATION = True
except ImportError:
    pass

# Prometheus metrics
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

CACHE_OPERATION_DURATION = Histogram(
    "cache_operation_duration_seconds",
    "Cache operation latency",
    ["operation", "status"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5),
)

ERROR_COUNTER = Counter(
    "application_errors_total",
    "Total application errors by type",
    ["error_type", "endpoint", "source"],
)

EXTERNAL_REQUEST_DURATION = Histogram(
    "external_request_duration_seconds",
    "External service request latency",
    ["service", "operation", "status"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 7.5, 10.0),
)

# Add new cache metrics
CACHE_HITS = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache_type"],  # redis, memory, etc.
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache_type"],
)

# Add external service error counter
EXTERNAL_SERVICE_ERRORS = Counter(
    "external_service_errors_total",
    "Total number of external service errors",
    ["service", "operation", "error_type"],
)


def setup_opentelemetry(app) -> None:
    """Configure OpenTelemetry with FastAPI integration.

    Args:
        app: FastAPI application instance
    """
    if not HAS_OTEL_INSTRUMENTATION:
        return

    # Create a resource with service information
    resource = Resource.create(
        {
            "service.name": settings.PROJECT_NAME,
            "service.version": settings.VERSION,
            "deployment.environment": settings.ENVIRONMENT,
            "deployment.region": settings.DEPLOYMENT_REGION,
        }
    )

    # Configure sampling based on environment
    if settings.ENVIRONMENT == "development":
        sampler = ParentBasedTraceIdRatio(1.0)
    else:
        sampler = ParentBasedTraceIdRatio(0.1)

    # Set up the tracer provider
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=sampler,
    )

    # Configure the OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        headers={},
    )
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Set the tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=tracer_provider,
        excluded_urls="health,metrics",
    )

    # Instrument other libraries
    RequestsInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument(
        tracer_provider=tracer_provider,
        enable_commenter=True,
        commenter_options={},
    )


def timing_middleware() -> Callable:
    """Create middleware for timing HTTP requests.

    Returns:
        Middleware function for FastAPI
    """

    async def middleware(request, call_next):
        start_time = time.perf_counter()
        response = None

        try:
            response = await call_next(request)
        except Exception:
            # Record error metrics
            endpoint = request.url.path
            for param_name, param_value in request.path_params.items():
                endpoint = endpoint.replace(str(param_value), f"{{{param_name}}}")

            HTTP_REQUEST_DURATION.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=500,
            ).observe(time.perf_counter() - start_time)

            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=500,
            ).inc()
            raise
        finally:
            if response is not None:
                duration = time.perf_counter() - start_time

                # Extract endpoint pattern (replace path parameters with placeholders)
                endpoint = request.url.path
                for param_name, param_value in request.path_params.items():
                    endpoint = endpoint.replace(str(param_value), f"{{{param_name}}}")

                # Record metrics
                HTTP_REQUEST_DURATION.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                ).observe(duration)

                HTTP_REQUESTS_TOTAL.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                ).inc()

        return response

    return middleware


def record_db_operation(
    operation: str, table: str, duration: float, status: str = "success"
) -> None:
    """Record database operation metrics.

    Args:
        operation: Type of operation (select, insert, update, delete)
        table: Database table name
        duration: Operation duration in seconds
        status: Operation status (success/error)
    """
    DB_OPERATION_DURATION.labels(
        operation=operation,
        table=table,
        status=status,
    ).observe(duration)


def record_db_pool_stats(in_use: int, available: int, overflow: int) -> None:
    """Record database connection pool statistics.

    Args:
        in_use: Number of connections currently in use
        available: Number of available connections
        overflow: Number of overflow connections
    """
    DB_POOL_STATS.labels("in_use").set(in_use)
    DB_POOL_STATS.labels("available").set(available)
    DB_POOL_STATS.labels("overflow").set(overflow)


def record_cache_operation(operation: str, duration: float, status: str = "success") -> None:
    """Record cache operation metrics.

    Args:
        operation: Type of operation (get, set, delete)
        duration: Operation duration in seconds
        status: Operation status (success/error)
    """
    CACHE_OPERATION_DURATION.labels(
        operation=operation,
        status=status,
    ).observe(duration)


def record_error(error_type: str, endpoint: str, source: str = "application") -> None:
    """Record application error metrics.

    Args:
        error_type: Type of error
        endpoint: Endpoint where error occurred
        source: Error source (application/database/external)
    """
    ERROR_COUNTER.labels(
        error_type=error_type,
        endpoint=endpoint,
        source=source,
    ).inc()


def record_external_request(
    service: str,
    operation: str,
    duration: float,
    status: str = "success",
    error_type: str = None,
) -> None:
    """Record external service request metrics.

    Args:
        service: External service name (e.g., supabase, weaviate)
        operation: Operation type
        duration: Request duration in seconds
        status: Request status (success/error)
        error_type: Type of error if request failed
    """
    EXTERNAL_REQUEST_DURATION.labels(
        service=service,
        operation=operation,
        status=status,
    ).observe(duration)

    if status == "error" and error_type:
        EXTERNAL_SERVICE_ERRORS.labels(
            service=service,
            operation=operation,
            error_type=error_type,
        ).inc()


def record_cache_hit(cache_type: str) -> None:
    """Record a cache hit.

    Args:
        cache_type: Type of cache (redis, memory, etc.)
    """
    CACHE_HITS.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str) -> None:
    """Record a cache miss.

    Args:
        cache_type: Type of cache (redis, memory, etc.)
    """
    CACHE_MISSES.labels(cache_type=cache_type).inc()


def get_metrics() -> str:
    """Generate OpenMetrics-compatible metrics output.

    Returns:
        Metrics in OpenMetrics format
    """
    return generate_latest(REGISTRY).decode("utf-8")
