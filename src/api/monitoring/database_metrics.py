"""Database monitoring and metrics collection.

This module provides database-specific monitoring, including connection pool statistics,
query performance tracking, and integration with OpenTelemetry for distributed tracing.
"""

import logging
from contextlib import contextmanager

from sqlalchemy.engine import Engine

from src.api.monitoring.database.handlers import register_query_listeners
from src.api.monitoring.database.pool import start_pool_stats_logging
from src.api.monitoring.metrics import record_error

logger = logging.getLogger(__name__)


def setup_database_monitoring(engine: Engine) -> None:
    """Set up database monitoring for a SQLAlchemy engine.

    Args:
        engine: SQLAlchemy engine instance
    """
    register_query_listeners(engine)
    start_pool_stats_logging(engine)


@contextmanager
def track_database_errors():
    """Context manager to track database errors and record metrics."""
    try:
        yield
    except Exception as e:
        record_error(
            error_type=type(e).__name__,
            endpoint="database",
            source="database",
        )
        raise
