"""Redis monitoring and metrics collection.

This module provides Redis-specific monitoring, including operation timing,
connection pool statistics, and cache hit/miss tracking.
"""

import logging
import time
from contextlib import contextmanager

from opentelemetry import trace
from redis import Redis
from redis.client import Pipeline
from redis.connection import ConnectionPool

from src.api.config.settings import settings
from src.api.monitoring.metrics import (
    CACHE_HITS,
    CACHE_MISSES,
    CACHE_OPERATION_DURATION,
    record_error,
)

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Try to import APScheduler, but don't fail if it's not available
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    logger.warning("APScheduler not available. Pool stats logging will be disabled.")


def setup_redis_monitoring(redis_client: Redis) -> None:
    """Set up Redis monitoring for a Redis client.

    Args:
        redis_client: Redis client instance
    """
    # Patch Redis methods to add monitoring
    _patch_redis_methods(redis_client)

    # Start periodic pool stats logging if available
    if isinstance(redis_client.connection_pool, ConnectionPool):
        _start_pool_stats_logging(redis_client.connection_pool)


def _patch_redis_methods(redis_client: Redis) -> None:
    """Patch Redis methods to add monitoring.

    Args:
        redis_client: Redis client instance
    """
    original_execute_command = redis_client.execute_command

    def monitored_execute_command(command_name, *args, **kwargs):
        """Wrapper for Redis command execution with monitoring."""
        start_time = time.perf_counter()
        success = True

        with tracer.start_as_current_span(
            "redis_operation",
            attributes={
                "redis.command": command_name,
                "redis.args": str(args),
            },
        ) as span:
            try:
                result = original_execute_command(command_name, *args, **kwargs)

                # Track cache hits/misses for GET operations
                if command_name.upper() == "GET":
                    if result is not None:
                        CACHE_HITS.labels(cache_type="redis").inc()
                    else:
                        CACHE_MISSES.labels(cache_type="redis").inc()

                return result

            except Exception as e:
                success = False
                record_error(
                    error_type=type(e).__name__,
                    endpoint="redis",
                    source="redis",
                )
                raise
            finally:
                duration = time.perf_counter() - start_time
                CACHE_OPERATION_DURATION.labels(
                    operation=command_name.lower(),
                    status="success" if success else "error",
                ).observe(duration)

                if span:
                    span.set_attribute("redis.duration", duration)

    redis_client.execute_command = monitored_execute_command


@contextmanager
def track_pipeline_operations(pipeline: Pipeline) -> None:
    """Context manager to track Redis pipeline operations.

    Args:
        pipeline: Redis pipeline instance
    """
    start_time = time.perf_counter()
    success = True

    with tracer.start_as_current_span(
        "redis_pipeline",
        attributes={
            "redis.pipeline_length": len(pipeline.command_stack),
        },
    ) as span:
        try:
            yield
        except Exception as e:
            success = False
            record_error(
                error_type=type(e).__name__,
                endpoint="redis_pipeline",
                source="redis",
            )
            raise
        finally:
            duration = time.perf_counter() - start_time
            CACHE_OPERATION_DURATION.labels(
                operation="pipeline",
                status="success" if success else "error",
            ).observe(duration)

            if span:
                span.set_attribute("redis.duration", duration)
                span.set_attribute("redis.commands", str(pipeline.command_stack))


def _start_pool_stats_logging(pool: ConnectionPool) -> None:
    """Start periodic logging of Redis connection pool statistics.

    Args:
        pool: Redis connection pool instance
    """
    if not HAS_APSCHEDULER:
        logger.warning("Pool stats logging disabled: APScheduler not available")
        return

    def log_pool_stats():
        """Log current pool statistics."""
        try:
            # Get pool statistics
            total = pool.max_connections
            in_use = len(pool._in_use_connections)
            available = len(pool._available_connections)

            # Log if approaching capacity
            if in_use > total * 0.8:  # 80% capacity
                logger.warning(
                    "Redis connection pool nearing capacity",
                    extra={
                        "in_use": in_use,
                        "available": available,
                        "total": total,
                    },
                )

        except Exception as e:
            logger.exception("Error logging Redis pool stats")
            record_error(
                error_type=type(e).__name__,
                endpoint="redis_pool",
                source="redis",
            )

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        log_pool_stats,
        "interval",
        seconds=settings.REDIS_POOL_STATS_INTERVAL,
        id="redis_pool_stats",
    )
    scheduler.start()
