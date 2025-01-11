"""Sentry configuration and initialization.

This module provides the main entry point for Sentry configuration and setup.
"""

from src.api.config.sentry.handlers import before_send
from src.api.config.sentry.integrations import get_sentry_integrations
from src.api.config.sentry.sampling import traces_sampler
from src.api.config.settings import settings

__all__ = ["init_sentry", "before_send", "traces_sampler"]


def init_sentry() -> None:
    """Initialize Sentry SDK with all configurations and integrations."""
    if not settings.SENTRY_DSN:
        return

    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        release=settings.VERSION,
        # Performance monitoring
        enable_tracing=True,
        traces_sampler=traces_sampler,
        # Data management
        send_default_pii=False,
        request_bodies="small",
        # Error filtering
        before_send=before_send,
        # Integrations
        integrations=get_sentry_integrations(),
        # Performance and profiling
        _experiments={
            "continuous_profiling_auto_start": True,
        },
        # Additional settings
        debug=settings.ENVIRONMENT == "development",
        max_breadcrumbs=settings.SENTRY_MAX_BREADCRUMBS,
        attach_stacktrace=settings.SENTRY_ATTACH_STACKTRACE,
        sample_rate=1.0,
        # Advanced settings
        shutdown_timeout=5,
        auto_enabling_integrations=True,
        default_integrations=True,
        propagate_traces=True,
    )
