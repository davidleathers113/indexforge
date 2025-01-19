"""Database connection pool monitoring.

This module handles monitoring and logging of database connection pool statistics.
It provides real-time tracking of connection pool health and utilization metrics.

Features:
- Connection pool utilization tracking
- Overflow detection and alerting
- Periodic statistics collection
- Integration with Prometheus metrics
- Capacity threshold monitoring
"""

import logging

from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool

from src.api.config.settings import settings
from src.api.monitoring.metrics import DB_POOL_STATS, record_error


logger = logging.getLogger(__name__)

# Pool health thresholds
POOL_CAPACITY_WARNING_THRESHOLD = 0.8  # 80% of max pool size
POOL_OVERFLOW_WARNING_THRESHOLD = 5  # Alert if more than 5 overflow connections


def start_pool_stats_logging(engine: Engine) -> None:
    """Start periodic logging of connection pool statistics.

    Sets up a scheduler to regularly collect and report pool statistics,
    including connection utilization, overflow status, and pool health metrics.

    Args:
        engine: SQLAlchemy engine instance to monitor

    Note:
        Requires APScheduler package. If not available, monitoring will be disabled
        but the application will continue to function.
    """
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
    except ImportError:
        logger.error("APScheduler not installed. Pool stats logging disabled.")
        return

    pool = engine.pool
    scheduler = AsyncIOScheduler()

    def log_pool_stats() -> None:
        """Log current pool statistics and record metrics.

        Collects and records various pool health metrics:
        - Connection utilization (in use, available, overflow)
        - Pool capacity percentage
        - Wait times for connections
        - Overflow connection count
        """
        try:
            # Basic pool stats
            in_use = pool.checkedin()
            available = pool.checkedout()
            overflow = pool.overflow()
            total = in_use + available + overflow

            # Record detailed metrics
            DB_POOL_STATS.labels("in_use").set(in_use)
            DB_POOL_STATS.labels("available").set(available)
            DB_POOL_STATS.labels("overflow").set(overflow)
            DB_POOL_STATS.labels("total").set(total)

            # Calculate and record utilization percentage
            if settings.DB_POOL_SIZE > 0:  # Avoid division by zero
                utilization = (total / settings.DB_POOL_SIZE) * 100
                DB_POOL_STATS.labels("utilization_percent").set(utilization)

            # Record pool health indicators
            record_pool_health_metrics(pool, total, overflow)

            # Log warnings for concerning conditions
            check_pool_health(in_use, available, overflow, total)

        except Exception as e:
            logger.exception("Error logging pool stats")
            record_error(
                error_type=type(e).__name__,
                endpoint="database_pool",
                source="database",
            )

    scheduler.add_job(
        log_pool_stats,
        "interval",
        seconds=settings.DB_POOL_STATS_INTERVAL,
        id="db_pool_stats",
    )
    scheduler.start()


def record_pool_health_metrics(pool: Pool, total: int, overflow: int) -> None:
    """Record additional pool health metrics.

    Args:
        pool: SQLAlchemy connection pool
        total: Total number of connections
        overflow: Number of overflow connections
    """
    try:
        # Record timeout and overflow metrics
        DB_POOL_STATS.labels("checkout_timeout_count").set(getattr(pool, "_timeout_count", 0))
        DB_POOL_STATS.labels("overflow_count").set(overflow)

        # Record pool capacity metrics
        if settings.DB_POOL_SIZE > 0:
            capacity_used = (total / settings.DB_POOL_SIZE) * 100
            DB_POOL_STATS.labels("capacity_used_percent").set(capacity_used)

    except Exception as e:
        logger.error(f"Error recording pool health metrics: {e}")


def check_pool_health(
    in_use: int,
    available: int,
    overflow: int,
    total: int,
) -> None:
    """Check pool health and log warnings for concerning conditions.

    Args:
        in_use: Number of connections in use
        available: Number of available connections
        overflow: Number of overflow connections
        total: Total number of connections
    """
    # Check capacity threshold
    if total > settings.DB_POOL_SIZE * POOL_CAPACITY_WARNING_THRESHOLD:
        logger.warning(
            "Database pool nearing capacity",
            extra={
                "in_use": in_use,
                "available": available,
                "overflow": overflow,
                "total": total,
                "capacity": settings.DB_POOL_SIZE,
            },
        )

    # Check overflow threshold
    if overflow > POOL_OVERFLOW_WARNING_THRESHOLD:
        logger.warning(
            "High number of overflow connections",
            extra={
                "overflow": overflow,
                "threshold": POOL_OVERFLOW_WARNING_THRESHOLD,
            },
        )

    # Check if available connections are low
    if available == 0 and total > 0:
        logger.warning(
            "No available connections in pool",
            extra={
                "in_use": in_use,
                "overflow": overflow,
                "total": total,
            },
        )
