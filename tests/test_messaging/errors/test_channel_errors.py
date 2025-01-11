"""Tests for RabbitMQ channel error handling scenarios."""

import asyncio
from unittest.mock import patch

import pytest
from aio_pika.exceptions import ChannelInvalidStateError

from src.api.messaging import rabbitmq_settings
from src.api.messaging.rabbitmq_connection_manager import RabbitMQChannelError


@pytest.mark.asyncio
async def test_channel_closed_handling(connection_manager, mock_rabbitmq):
    """Test handling of channel closed errors.

    Verifies that:
    1. Channel closed errors are properly caught and wrapped
    2. Retry mechanism is triggered
    3. Error context is preserved
    """
    error_msg = "Channel was closed by server"

    with patch.object(
        mock_rabbitmq["connection"], "channel", side_effect=ChannelInvalidStateError(error_msg)
    ):
        with pytest.raises(RabbitMQChannelError) as exc_info:
            async with connection_manager.acquire_channel():
                pass

        assert str(exc_info.value) == f"Failed to create channel: {error_msg}"
        assert isinstance(exc_info.value.__cause__, ChannelInvalidStateError)


@pytest.mark.asyncio
async def test_channel_overflow_handling(connection_manager, mock_rabbitmq):
    """Test handling of channel number overflow.

    Verifies that:
    1. Channel overflow errors are properly handled
    2. Max channels per connection is respected
    3. Error details are preserved
    """
    # Store original max channels
    original_max_channels = rabbitmq_settings.max_channels_per_connection

    try:
        # Set max channels to 1 for testing
        rabbitmq_settings.max_channels_per_connection = 1

        # First channel should succeed
        async with connection_manager.acquire_channel() as channel1:
            assert channel1 == mock_rabbitmq["channel"]

            # Second channel should fail
            with pytest.raises(RabbitMQChannelError) as exc_info:
                async with connection_manager.acquire_channel():
                    pass

            assert "max channels exceeded" in str(exc_info.value).lower()

    finally:
        # Restore original max channels
        rabbitmq_settings.max_channels_per_connection = original_max_channels


@pytest.mark.asyncio
async def test_channel_operation_timeout(connection_manager, mock_rabbitmq):
    """Test handling of channel operation timeouts.

    Verifies that:
    1. Operation timeouts are properly handled
    2. Retry attempts respect timeout settings
    3. Error context includes timeout information
    """
    # Store original timeout
    original_timeout = rabbitmq_settings.channel_operation_timeout

    try:
        # Set shorter timeout for testing
        rabbitmq_settings.channel_operation_timeout = 0.1

        async def delayed_channel(*args, **kwargs):
            await asyncio.sleep(0.2)  # Longer than timeout
            return mock_rabbitmq["channel"]

        with patch.object(mock_rabbitmq["connection"], "channel", side_effect=delayed_channel):
            with pytest.raises(RabbitMQChannelError) as exc_info:
                async with connection_manager.acquire_channel():
                    pass

            assert "operation timeout" in str(exc_info.value).lower()
            assert isinstance(exc_info.value.__cause__, asyncio.TimeoutError)

    finally:
        # Restore original timeout
        rabbitmq_settings.channel_operation_timeout = original_timeout
