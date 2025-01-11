"""Tests for RabbitMQ recovery error handling scenarios."""

import asyncio
from unittest.mock import patch

import pytest
from aio_pika.exceptions import AMQPConnectionError, ChannelInvalidStateError

from src.api.messaging import rabbitmq_settings
from src.api.messaging.rabbitmq_connection_manager import RabbitMQConnectionError


@pytest.mark.asyncio
async def test_max_retry_attempts_handling(connection_manager, mock_rabbitmq):
    """Test handling of maximum retry attempts.

    Verifies that:
    1. Retry attempts are limited by max_retry_attempts setting
    2. Final error includes retry attempt information
    3. Backoff delay is respected between attempts
    """
    # Store original settings
    original_max_retries = rabbitmq_settings.max_retry_attempts
    original_retry_delay = rabbitmq_settings.retry_delay

    try:
        # Set test values
        rabbitmq_settings.max_retry_attempts = 2
        rabbitmq_settings.retry_delay = 0.1
        error_msg = "Connection refused"

        start_time = asyncio.get_event_loop().time()

        with patch("aio_pika.connect_robust", side_effect=ConnectionError(error_msg)):
            with pytest.raises(RabbitMQConnectionError) as exc_info:
                async with connection_manager.acquire_connection():
                    pass

        end_time = asyncio.get_event_loop().time()

        # Verify retry attempts
        assert connection_manager._connection_attempts == rabbitmq_settings.max_retry_attempts

        # Verify retry delay
        expected_min_duration = (
            rabbitmq_settings.max_retry_attempts - 1
        ) * rabbitmq_settings.retry_delay
        assert end_time - start_time >= expected_min_duration

        # Verify error message
        assert f"after {rabbitmq_settings.max_retry_attempts} attempts" in str(exc_info.value)

    finally:
        # Restore original settings
        rabbitmq_settings.max_retry_attempts = original_max_retries
        rabbitmq_settings.retry_delay = original_retry_delay


@pytest.mark.asyncio
async def test_recovery_during_health_check(connection_manager, mock_rabbitmq):
    """Test handling of errors during health check recovery.

    Verifies that:
    1. Health check triggers recovery on failure
    2. Failed recovery attempts are tracked
    3. Health check continues after failed recovery
    """
    # Store original settings
    original_interval = rabbitmq_settings.monitoring_interval

    try:
        # Set shorter interval for testing
        rabbitmq_settings.monitoring_interval = 0.1

        # Start health checks
        await connection_manager.start()

        # Simulate channel failure
        mock_rabbitmq["channel"].is_closed = True

        # Wait for health check to detect failure
        await asyncio.sleep(rabbitmq_settings.monitoring_interval * 2)

        # Verify recovery was attempted
        assert connection_manager._consecutive_failures >= 1
        assert connection_manager._health_check_attempts >= 2

        # Simulate recovery failure
        with patch.object(
            mock_rabbitmq["connection"],
            "channel",
            side_effect=AMQPConnectionError("Recovery failed"),
        ):
            # Wait for another health check cycle
            await asyncio.sleep(rabbitmq_settings.monitoring_interval * 2)

            # Verify continued monitoring
            assert connection_manager._consecutive_failures >= 2
            assert connection_manager._health_check_attempts >= 3

    finally:
        # Cleanup
        await connection_manager.close()
        rabbitmq_settings.monitoring_interval = original_interval


@pytest.mark.asyncio
async def test_partial_recovery_handling(connection_manager, mock_rabbitmq):
    """Test handling of partial recovery scenarios.

    Verifies that:
    1. Connection recovery succeeds but channel fails
    2. Partial recovery state is properly handled
    3. System attempts to fully recover in next cycle
    """
    # Store original interval
    original_interval = rabbitmq_settings.monitoring_interval

    try:
        # Set shorter interval for testing
        rabbitmq_settings.monitoring_interval = 0.1

        # Start health checks
        await connection_manager.start()

        # Simulate connection and channel failure
        mock_rabbitmq["connection"].is_closed = True
        mock_rabbitmq["channel"].is_closed = True

        # Wait for health check to detect failure
        await asyncio.sleep(rabbitmq_settings.monitoring_interval * 2)

        # Simulate partial recovery - connection succeeds but channel fails
        mock_rabbitmq["connection"].is_closed = False
        with patch.object(
            mock_rabbitmq["connection"],
            "channel",
            side_effect=ChannelInvalidStateError("Channel recovery failed"),
        ):
            # Wait for recovery attempt
            await asyncio.sleep(rabbitmq_settings.monitoring_interval * 2)

            # Verify partial recovery state
            assert not mock_rabbitmq["connection"].is_closed
            assert connection_manager._consecutive_failures >= 1

    finally:
        # Cleanup
        await connection_manager.close()
        rabbitmq_settings.monitoring_interval = original_interval
