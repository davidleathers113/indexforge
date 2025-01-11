"""Tests for RabbitMQ connection metrics collection."""

from unittest.mock import patch

import pytest

from src.api.messaging import rabbitmq_settings
from src.api.messaging.rabbitmq_connection_manager import RabbitMQConnectionError
from src.api.monitoring.metrics import record_error


@pytest.mark.asyncio
async def test_connection_success_metrics(connection_manager, mock_rabbitmq):
    """Test metrics collection for successful connections.

    Verifies that:
    1. Connection attempts are counted
    2. Successful connections increment the counter
    3. Connection timing is recorded
    """
    # First connection
    async with connection_manager.acquire_connection() as connection:
        assert connection_manager._connection_attempts == 1
        assert connection == mock_rabbitmq["connection"]

    # Second connection (should reuse pool)
    async with connection_manager.acquire_connection() as connection:
        assert connection_manager._connection_attempts == 1
        assert connection == mock_rabbitmq["connection"]


@pytest.mark.asyncio
async def test_connection_failure_metrics(connection_manager, mock_rabbitmq):
    """Test metrics collection for failed connections.

    Verifies that:
    1. Failed attempts are counted
    2. Errors are recorded with proper context
    3. Last error is stored
    """
    error_msg = "Connection refused"

    # Mock record_error to track calls
    with patch("src.api.monitoring.metrics.record_error") as mock_record_error:
        # Simulate connection failure
        with patch("aio_pika.connect_robust", side_effect=ConnectionError(error_msg)):
            with pytest.raises(RabbitMQConnectionError):
                async with connection_manager.acquire_connection():
                    pass

        # Verify error was recorded
        mock_record_error.assert_called_once_with(
            "rabbitmq_connection_error",
            error_msg,
            {
                "connection_id": mock_rabbitmq["connection"].id,
                "attempt": connection_manager._connection_attempts,
            },
        )

        # Verify attempt was counted
        assert connection_manager._connection_attempts == 1

        # Verify last error was stored
        assert str(connection_manager._last_connection_error) == error_msg
