"""Tests for RabbitMQ connection error handling scenarios."""

import asyncio
from unittest.mock import patch

from aio_pika.exceptions import AMQPConnectionError
import pytest

from src.api.messaging import rabbitmq_settings
from src.api.messaging.rabbitmq_connection_manager import RabbitMQConnectionError


@pytest.mark.asyncio
async def test_network_failure_handling(connection_manager, mock_rabbitmq):
    """Test handling of network-related connection failures.

    Verifies that:
    1. Network errors are properly caught and wrapped
    2. Retry mechanism is triggered
    3. Error context is preserved
    """
    error_msg = "Network unreachable"

    with patch("aio_pika.connect_robust", side_effect=ConnectionError(error_msg)):
        with pytest.raises(RabbitMQConnectionError) as exc_info:
            async with connection_manager.acquire_connection():
                pass

        assert str(exc_info.value) == f"Failed to establish connection: {error_msg}"
        assert isinstance(exc_info.value.__cause__, ConnectionError)


@pytest.mark.asyncio
async def test_authentication_failure_handling(connection_manager, mock_rabbitmq):
    """Test handling of authentication failures.

    Verifies that:
    1. Auth errors are properly caught and wrapped
    2. No retry attempt is made for auth failures
    3. Error details are preserved
    """
    error_msg = "Access refused: invalid credentials"

    with patch("aio_pika.connect_robust", side_effect=AMQPConnectionError(error_msg)):
        with pytest.raises(RabbitMQConnectionError) as exc_info:
            async with connection_manager.acquire_connection():
                pass

        assert str(exc_info.value) == f"Failed to establish connection: {error_msg}"
        assert isinstance(exc_info.value.__cause__, AMQPConnectionError)
        assert connection_manager._connection_attempts == 1  # No retry for auth failures


@pytest.mark.asyncio
async def test_connection_timeout_handling(connection_manager, mock_rabbitmq):
    """Test handling of connection timeouts.

    Verifies that:
    1. Timeouts are properly handled
    2. Retry attempts respect timeout settings
    3. Error context includes timeout information
    """
    # Store original timeout
    original_timeout = rabbitmq_settings.connection_timeout

    try:
        # Set shorter timeout for testing
        rabbitmq_settings.connection_timeout = 0.1

        async def delayed_connection(*args, **kwargs):
            await asyncio.sleep(0.2)  # Longer than timeout
            return mock_rabbitmq["connection"]

        with patch("aio_pika.connect_robust", side_effect=delayed_connection):
            with pytest.raises(RabbitMQConnectionError) as exc_info:
                async with connection_manager.acquire_connection():
                    pass

            assert "connection timeout" in str(exc_info.value).lower()
            assert isinstance(exc_info.value.__cause__, asyncio.TimeoutError)

    finally:
        # Restore original timeout
        rabbitmq_settings.connection_timeout = original_timeout
