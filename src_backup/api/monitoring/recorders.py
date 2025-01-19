"""Metric recording functions.

This module provides functions for recording various metrics throughout the application.
"""

from src.api.monitoring.prometheus_metrics import (
    CACHE_HITS,
    CACHE_MISSES,
    CACHE_OPERATION_DURATION,
    DB_OPERATION_DURATION,
    DB_POOL_STATS,
    ERROR_COUNTER,
    EXTERNAL_REQUEST_DURATION,
    EXTERNAL_SERVICE_ERRORS,
)


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
