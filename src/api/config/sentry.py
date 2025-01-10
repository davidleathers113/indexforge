"""Sentry configuration and setup.

This module provides a centralized configuration for Sentry error tracking and performance monitoring,
including environment-specific settings, data filtering, and integration setup.
"""

import logging
import os
from typing import Any, Dict, Optional

import sentry_sdk
from sentry_sdk.integrations.asyncpg import AsyncPGIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from src.api.config.settings import settings
from src.api.monitoring.metrics import record_error


def get_git_commit() -> Optional[str]:
    """Get the current git commit hash."""
    try:
        with open(".git/HEAD") as f:
            ref = f.read().strip()
            if ref.startswith("ref: "):
                ref_path = os.path.join(".git", ref[5:])
                with open(ref_path) as f:
                    return f.read().strip()
            return ref
    except (FileNotFoundError, IOError):
        return None


def get_transaction_name(request) -> str:
    """Generate consistent transaction names.

    Args:
        request: FastAPI request object

    Returns:
        Formatted transaction name
    """
    import re

    path = request.url.path
    # Replace numeric IDs with {id} placeholder
    path = re.sub(r"/\d+", "/{id}", path)
    return f"{request.method} {path}"


def before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Filter and modify events before sending to Sentry."""
    # Ignore common errors that don't need tracking
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]

        # Add custom fingerprinting for specific errors
        if isinstance(exc_value, ValueError):
            event["fingerprint"] = ["value-error", str(exc_value)]
        elif isinstance(exc_value, KeyError):
            event["fingerprint"] = ["key-error", str(exc_value)]
        elif isinstance(exc_value, ConnectionError):
            event["fingerprint"] = ["connection-error", str(exc_value)]

        # Record error metrics
        if "transaction" in event:
            record_error(
                error_type=exc_type.__name__,
                endpoint=event["transaction"],
                source="application",
            )

        # Ignore certain errors in development
        if settings.ENVIRONMENT == "development":
            if isinstance(exc_value, (KeyError, ValueError)):
                return None

    # Handle errors without exception info
    elif event.get("level") == "error":
        event["fingerprint"] = ["unhandled-error", event.get("message", "unknown")]
        if "transaction" in event:
            record_error(
                error_type="UnhandledException",
                endpoint=event["transaction"],
                source="application",
            )

    # Strip sensitive data from request headers
    if "request" in event and "headers" in event["request"]:
        event["request"]["headers"] = {
            k: v
            for k, v in event["request"]["headers"].items()
            if k.lower() not in ("authorization", "cookie", "x-api-key")
        }

    # Add deployment context
    event["contexts"]["deployment"] = {
        "environment": settings.ENVIRONMENT,
        "region": settings.DEPLOYMENT_REGION,
        "version": settings.VERSION,
        "commit": get_git_commit(),
    }

    # Add performance context if available
    if "transaction" in event:
        event["contexts"]["performance"] = {
            "threshold": settings.PERFORMANCE_THRESHOLDS["p95_latency_ms"],
            "apdex_target": settings.PERFORMANCE_THRESHOLDS["apdex_threshold"],
        }

    return event


def traces_sampler(sampling_context: Dict[str, Any]) -> float:
    """Determine trace sampling rate based on context."""
    if settings.ENVIRONMENT == "development":
        return 1.0

    # If this is part of an existing trace, respect the parent decision
    if sampling_context.get("parent_sampled"):
        return 1.0

    # Get the transaction name if available
    transaction_name = sampling_context.get("transaction_context", {}).get("name", "")

    # Sample high-throughput endpoints at a lower rate
    if transaction_name.startswith(("GET /health", "GET /metrics")):
        return 0.01

    # Sample important endpoints at a higher rate
    if transaction_name.startswith(("POST /api/v1/search", "POST /api/v1/documents")):
        return 0.5

    # Default sampling rates by environment
    return {
        "production": 0.1,  # 10% of transactions
        "staging": 0.3,  # 30% of transactions
        "development": 1.0,  # 100% of transactions
    }.get(settings.ENVIRONMENT, 0.1)


def init_sentry() -> None:
    """Initialize Sentry SDK with all configurations and integrations."""
    if not settings.SENTRY_DSN:
        return

    # Initialize logging integration
    logging_integration = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors as events
    )

    # Initialize Sentry SDK
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        release=settings.VERSION,
        # Performance monitoring
        enable_tracing=True,
        traces_sampler=traces_sampler,
        # Data management
        send_default_pii=False,
        request_bodies="small",  # Only capture requests under 10kb
        # Error filtering
        before_send=before_send,
        # Integrations
        integrations=[
            FastApiIntegration(
                transaction_style="endpoint",
                transaction_name_callback=get_transaction_name,
            ),
            AsyncPGIntegration(
                connect_string=True,
                enable_commenter=True,
            ),
            SqlalchemyIntegration(
                connect_string=True,
                keep_context=True,
            ),
            RedisIntegration(),
            logging_integration,
        ],
        # Performance and profiling
        _experiments={
            "continuous_profiling_auto_start": True,
        },
        # Additional settings
        debug=settings.ENVIRONMENT == "development",
        max_breadcrumbs=settings.SENTRY_MAX_BREADCRUMBS,
        attach_stacktrace=settings.SENTRY_ATTACH_STACKTRACE,
        sample_rate=1.0,  # Error sampling (different from transaction sampling)
        # Advanced settings
        shutdown_timeout=5,  # Wait up to 5 seconds for events to be sent
        auto_enabling_integrations=True,
        default_integrations=True,
        propagate_traces=True,
    )
