"""Sentry integrations configuration.

This module configures various Sentry integrations for monitoring and logging.
"""

import logging
from typing import List

from sentry_sdk.integrations.asyncpg import AsyncPGIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from src.api.config.sentry.utils import get_transaction_name


def get_sentry_integrations() -> List:
    """Get configured Sentry integrations."""
    # Initialize logging integration
    logging_integration = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors as events
    )

    return [
        FastApiIntegration(
            transaction_style="endpoint",
            transaction_name_callback=get_transaction_name,
        ),
        AsyncPGIntegration(),  # Removed unsupported args
        SqlalchemyIntegration(keep_context=True),  # Removed unsupported arg
        RedisIntegration(),
        logging_integration,
    ]
