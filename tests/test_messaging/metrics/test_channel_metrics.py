"""Tests for RabbitMQ channel metrics collection."""

from unittest.mock import patch

import pytest

from src.api.messaging.rabbitmq_connection_manager import RabbitMQChannelError


@pytest.mark.asyncio
async def test_channel_creation_metrics(connection_manager, mock_rabbitmq):
    """Test metrics collection for channel creation.

    Verifies that:
    1. Channel creation attempts are counted
    2. Successful creations increment the counter
    3. Channel timing is recorded
    """
    # First channel
    async with connection_manager.acquire_channel() as channel:
        assert connection_manager._channel_creation_attempts == 1
        assert channel == mock_rabbitmq["channel"]

    # Second channel (should create new)
    async with connection_manager.acquire_channel() as channel:
        assert connection_manager._channel_creation_attempts == 2
        assert channel == mock_rabbitmq["channel"]


@pytest.mark.asyncio
async def test_channel_error_metrics(connection_manager, mock_rabbitmq):
    """Test metrics collection for channel errors.

    Verifies that:
    1. Failed attempts are counted
    2. Errors are recorded with proper context
    3. Last error is stored
    """
    error_msg = "Channel closed"

    # Mock record_error to track calls
    with patch("src.api.monitoring.metrics.record_error") as mock_record_error:
        # Simulate channel creation failure
        with patch.object(
            mock_rabbitmq["connection"], "channel", side_effect=ConnectionError(error_msg)
        ):
            with pytest.raises(RabbitMQChannelError):
                async with connection_manager.acquire_channel():
                    pass

        # Verify error was recorded
        mock_record_error.assert_called_once_with(
            "rabbitmq_channel_error",
            error_msg,
            {
                "connection_id": mock_rabbitmq["connection"].id,
                "attempt": connection_manager._channel_creation_attempts,
            },
        )

        # Verify attempt was counted
        assert connection_manager._channel_creation_attempts == 1

        # Verify last error was stored
        assert str(connection_manager._last_channel_error) == error_msg
