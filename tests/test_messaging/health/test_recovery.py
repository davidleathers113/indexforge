"""Tests for RabbitMQ health check recovery scenarios."""

import asyncio

import pytest

from src.api.messaging import rabbitmq_settings


@pytest.mark.asyncio
async def test_health_check_recovery(connection_manager, mock_rabbitmq):
    """Test health check recovery after connection failures.

    This test verifies that:
    1. Health checks detect connection failures
    2. The system attempts to recover from failures
    3. Recovery is successful when connection is restored
    """
    # Store original monitoring interval
    original_interval = rabbitmq_settings.monitoring_interval

    try:
        # Set shorter interval for testing
        rabbitmq_settings.monitoring_interval = 0.1

        # Start health checks
        await connection_manager.start()
        initial_call_count = mock_rabbitmq["connection"].channel.call_count

        # Simulate connection failure
        mock_rabbitmq["channel"].is_closed = True
        await asyncio.sleep(rabbitmq_settings.monitoring_interval * 2)

        # Verify failure was detected
        failure_call_count = mock_rabbitmq["connection"].channel.call_count
        assert failure_call_count > initial_call_count

        # Simulate recovery
        mock_rabbitmq["channel"].is_closed = False
        await asyncio.sleep(rabbitmq_settings.monitoring_interval * 2)

        # Verify recovery occurred
        recovery_call_count = mock_rabbitmq["connection"].channel.call_count
        assert recovery_call_count > failure_call_count

    finally:
        # Cleanup
        await connection_manager.close()
        rabbitmq_settings.monitoring_interval = original_interval
