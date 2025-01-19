"""Database query event handlers.

This module provides handlers for database query events, including timing and tracing.
It integrates with OpenTelemetry for distributed tracing and Prometheus for metrics collection.

Key Features:
- Query timing and performance tracking
- Slow query detection and logging
- OpenTelemetry trace spans for each query
- Automatic table name and operation type detection
- Error tracking and reporting
"""

import logging
import time
from typing import Any, TypeAlias

from opentelemetry import trace
from opentelemetry.trace import Span
from sqlalchemy.engine import Connection, Cursor, Engine
from sqlalchemy.event import listen

from src.api.config.settings import settings
from src.api.monitoring.database.utils import extract_table_name, get_operation_type
from src.api.monitoring.metrics import DB_OPERATION_DURATION, record_error


# Type aliases for better readability
QueryParameters: TypeAlias = dict[str, Any] | tuple[Any, ...] | list[Any]
ExecutionContext: TypeAlias = Any  # SQLAlchemy execution context is complex and varies by version

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def register_query_listeners(engine: Engine) -> None:
    """Register query event listeners for a SQLAlchemy engine.

    This function sets up the event listeners that will track query execution,
    including timing, tracing, and metric collection.

    Args:
        engine: SQLAlchemy engine instance to monitor

    Note:
        The listeners are registered for both before and after query execution
        to accurately measure query duration and maintain trace context.
    """
    listen(engine, "before_cursor_execute", _before_cursor_execute)
    listen(engine, "after_cursor_execute", _after_cursor_execute)


def _before_cursor_execute(
    conn: Connection,
    cursor: Cursor,
    statement: str,
    parameters: QueryParameters,
    context: ExecutionContext,
    executemany: bool,
) -> None:
    """Event listener for query start.

    Captures the start time of the query and creates an OpenTelemetry span
    for tracing. The span includes query details like the SQL statement,
    parameters, and operation type.

    Args:
        conn: Database connection being used
        cursor: Database cursor that will execute the query
        statement: Raw SQL statement to be executed
        parameters: Query parameters/values to be bound
        context: SQLAlchemy execution context
        executemany: Whether this is a bulk operation

    Note:
        The start time and span are stored in the connection info dictionary
        to be retrieved later by the after_cursor_execute handler.
    """
    # Store the start time in the connection info
    conn.info.setdefault("query_start_time", {})
    conn.info["query_start_time"][statement] = time.perf_counter()

    # Create a span for the query
    with tracer.start_as_current_span(
        "db_query",
        attributes={
            "db.statement": statement,
            "db.parameters": str(parameters),
            "db.operation": get_operation_type(statement),
            "db.executemany": executemany,
        },
    ) as span:
        # Store the span in connection info for later reference
        conn.info.setdefault("current_spans", {})
        conn.info["current_spans"][statement] = span


def _after_cursor_execute(
    conn: Connection,
    cursor: Cursor,
    statement: str,
    parameters: QueryParameters,
    context: ExecutionContext,
    executemany: bool,
) -> None:
    """Event listener for query completion.

    Calculates query duration, records metrics, and handles tracing span completion.
    Also detects and logs slow queries based on configured thresholds.

    Args:
        conn: Database connection that was used
        cursor: Database cursor that executed the query
        statement: Raw SQL statement that was executed
        parameters: Query parameters/values that were bound
        context: SQLAlchemy execution context
        executemany: Whether this was a bulk operation

    Note:
        - Query duration is measured using high-resolution performance counter
        - Slow queries are logged with detailed context for debugging
        - Metrics are recorded with operation type and table name labels
        - Any errors during monitoring are caught and recorded separately
    """
    try:
        # Calculate query duration
        start_time = conn.info["query_start_time"].pop(statement, None)
        if start_time is not None:
            duration = time.perf_counter() - start_time

            # Record metrics
            operation = get_operation_type(statement)
            table = extract_table_name(statement)

            DB_OPERATION_DURATION.labels(
                operation=operation,
                table=table,
                status="success",
            ).observe(duration)

            # Log slow queries
            if duration > settings.DB_SLOW_QUERY_THRESHOLD:
                logger.warning(
                    "Slow query detected",
                    extra={
                        "duration": duration,
                        "statement": statement,
                        "operation": operation,
                        "table": table,
                    },
                )

            # Update span if it exists
            span: Span | None = conn.info.get("current_spans", {}).pop(statement, None)
            if span:
                span.set_attribute("db.duration", duration)

    except Exception as e:
        logger.exception("Error in query monitoring")
        record_error(
            error_type=type(e).__name__,
            endpoint="database",
            source="database",
        )
