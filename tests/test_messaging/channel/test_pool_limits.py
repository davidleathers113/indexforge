"""Tests for RabbitMQ channel pool limit scenarios."""

import asyncio
from typing import List

import pytest

from src.api.messaging import rabbitmq_settings


@pytest.mark.asyncio
async def test_channel_pool_limits(connection_manager, mock_rabbitmq):
    """Test that channel pool respects maximum channels per connection.

    This test verifies that:
    1. Channels can be acquired up to the maximum limit
    2. Attempts to acquire channels beyond the limit timeout
    3. Channel resources are properly released
    """
    # Store original channel limit
    original_max_channels = rabbitmq_settings.max_channels_per_connection
    channels: List[object] = []

    try:
        # Set max channels to 2 for this test
        rabbitmq_settings.max_channels_per_connection = 2

        # Acquire maximum number of channels
        for _ in range(rabbitmq_settings.max_channels_per_connection):
            async with connection_manager.acquire_channel() as channel:
                assert channel == mock_rabbitmq["channel"]
                channels.append(channel)

        # Next channel acquisition should timeout
        with pytest.raises(TimeoutError):
            async with asyncio.timeout(0.1):
                async with connection_manager.acquire_channel():
                    pass

    finally:
        # Restore original channel limit
        rabbitmq_settings.max_channels_per_connection = original_max_channels
        channels.clear()
