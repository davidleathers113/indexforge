"""Sentry sampling configuration.

This module handles trace sampling decisions based on context and environment.
"""

from typing import Any, Dict

from src.api.config.settings import settings


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
