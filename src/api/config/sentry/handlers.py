"""Sentry event handlers and processors.

This module handles event processing, error handling, and context enrichment for Sentry events.
"""

import json
import os
from typing import Any, Dict, Optional

from src.api.config.sentry.utils import get_git_commit
from src.api.config.settings import settings
from src.api.monitoring.metrics import record_error


def _get_error_fingerprint(exc_value: Exception, event: Dict[str, Any]) -> list:
    """Generate error fingerprint based on exception type."""
    if isinstance(exc_value, ValueError):
        error_msg = str(exc_value)
        if "field" in error_msg.lower():
            field_name = error_msg.split()[0]
            return ["validation-error", field_name]
        return ["value-error", str(exc_value)]
    elif isinstance(exc_value, KeyError):
        return ["key-error", str(exc_value).strip("'")]
    elif isinstance(exc_value, ConnectionError):
        if hasattr(exc_value, "host"):
            return ["connection-error", str(exc_value.host)]
        return ["connection-error", str(exc_value)]
    elif isinstance(exc_value, TimeoutError):
        return ["timeout-error", event.get("transaction", "unknown")]
    elif isinstance(exc_value, PermissionError):
        return ["permission-error", str(exc_value)]
    elif isinstance(exc_value, FileNotFoundError):
        path = str(exc_value).split(": ")[1] if ": " in str(exc_value) else str(exc_value)
        dir_path = os.path.dirname(path)
        return ["file-error", dir_path]
    elif isinstance(exc_value, json.JSONDecodeError):
        return ["json-error", exc_value.msg]
    elif isinstance(exc_value, AssertionError):
        module = exc_value.__class__.__module__
        return ["assertion-error", module]
    return None


def _get_message_fingerprint(message: str) -> list:
    """Generate fingerprint based on error message pattern."""
    if "database" in message.lower():
        return ["database-error", message[:50]]
    elif "timeout" in message.lower():
        return ["timeout-error", message[:50]]
    elif "permission" in message.lower():
        return ["permission-error", message[:50]]
    return ["unhandled-error", message[:50]]


def before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Filter and modify events before sending to Sentry."""
    # Handle exception events
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]

        # Add fingerprint based on error type
        fingerprint = _get_error_fingerprint(exc_value, event)
        if fingerprint:
            event["fingerprint"] = fingerprint

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

    # Handle non-exception error events
    elif event.get("level") == "error":
        message = event.get("message", "unknown")
        event["fingerprint"] = _get_message_fingerprint(message)

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
