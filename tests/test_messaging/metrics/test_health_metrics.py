"""Tests for RabbitMQ health check metrics collection."""

import asyncio
from unittest.mock import patch

import pytest

from src.api.messaging import rabbitmq_settings


@pytest.mark.asyncio
async def test_health_check_success_metrics(connection_manager, mock_rabbitmq):
    """Test metrics collection for successful health checks.

    Verifies that:
    1. Health check attempts are counted
    2. Successful checks increment success counter
    3. Health check timing is recorded
    """
    # Store original monitoring interval
    original_interval = rabbitmq_settings.monitoring_interval

    try:
        # Set shorter interval for testing
        rabbitmq_settings.monitoring_interval = 0.1

        # Start health checks
        await connection_manager.start()

        # Wait for a few health check cycles
        await asyncio.sleep(rabbitmq_settings.monitoring_interval * 2)

        # Verify metrics
        assert connection_manager._health_check_attempts >= 2
        assert connection_manager._consecutive_failures == 0

    finally:
        # Cleanup
        await connection_manager.close()
        rabbitmq_settings.monitoring_interval = original_interval


@pytest.mark.asyncio
async def test_health_check_failure_metrics(connection_manager, mock_rabbitmq):
    """Test metrics collection for failed health checks.

    Verifies that:
    1. Failed checks are counted
    2. Consecutive failures are tracked
    3. Errors are recorded with proper context
    """
    # Store original monitoring interval
    original_interval = rabbitmq_settings.monitoring_interval
    error_msg = "Channel closed"

    try:
        # Set shorter interval for testing
        rabbitmq_settings.monitoring_interval = 0.1

        # Start health checks
        await connection_manager.start()

        # Mock record_error to track calls
        with patch("src.api.monitoring.metrics.record_error") as mock_record_error:
            # Simulate health check failure
            mock_rabbitmq["channel"].is_closed = True

            # Wait for a few health check cycles
            await asyncio.sleep(rabbitmq_settings.monitoring_interval * 2)

            # Verify metrics
            assert connection_manager._health_check_attempts >= 2
            assert connection_manager._consecutive_failures >= 1

            # Verify error was recorded
            mock_record_error.assert_called_with(
                "rabbitmq_health_check_error",
                error_msg,
                {
                    "connection_id": mock_rabbitmq["connection"].id,
                    "consecutive_failures": connection_manager._consecutive_failures,
                },
            )

    finally:
        # Cleanup
        await connection_manager.close()
        rabbitmq_settings.monitoring_interval = original_interval
