"""Tests for RabbitMQ connection management."""

import asyncio
from unittest.mock import patch

import pytest

from src.api.messaging import rabbitmq_settings
from src.api.messaging.rabbitmq_connection_manager import RabbitMQConnectionError


@pytest.mark.asyncio
async def test_create_connection(connection_manager, mock_rabbitmq):
    """Test connection creation."""
    async with connection_manager.acquire_connection() as connection:
        assert connection == mock_rabbitmq["connection"]
        mock_rabbitmq["connect"].assert_called_once_with(
            **rabbitmq_settings.get_connection_parameters()
        )


@pytest.mark.asyncio
async def test_create_channel(connection_manager, mock_rabbitmq):
    """Test channel creation."""
    async with connection_manager.acquire_channel() as channel:
        assert channel == mock_rabbitmq["channel"]
        mock_rabbitmq["channel"].set_qos.assert_called_once_with(
            prefetch_count=rabbitmq_settings.prefetch_count
        )


@pytest.mark.asyncio
async def test_health_check(connection_manager, mock_rabbitmq):
    """Test health check functionality."""
    # Start health check
    await connection_manager.start()

    # Wait for at least one health check
    await asyncio.sleep(rabbitmq_settings.monitoring_interval + 0.1)

    # Verify channel was created and checked
    assert mock_rabbitmq["connection"].channel.called

    # Clean up
    await connection_manager.close()


@pytest.mark.asyncio
async def test_connection_error_handling(connection_manager):
    """Test error handling during connection creation."""
    with patch("aio_pika.connect_robust", side_effect=ConnectionError("Connection failed")):
        with pytest.raises(
            RabbitMQConnectionError, match="Failed to acquire connection: Connection failed"
        ):
            async with connection_manager.acquire_connection():
                pass


@pytest.mark.asyncio
async def test_channel_error_handling(connection_manager, mock_rabbitmq):
    """Test error handling during channel creation."""
    mock_rabbitmq["connection"].channel.side_effect = Exception("Channel creation failed")

    with pytest.raises(Exception, match="Channel creation failed"):
        async with connection_manager.acquire_channel():
            pass


@pytest.mark.asyncio
async def test_connection_pool_reuse(connection_manager, mock_rabbitmq):
    """Test that connections are reused from the pool."""
    # First connection
    async with connection_manager.acquire_connection():
        pass

    # Second connection should reuse the pool
    async with connection_manager.acquire_connection():
        pass

    # Verify connect_robust was called only once
    assert mock_rabbitmq["connect"].call_count == 1


@pytest.mark.asyncio
async def test_connection_manager_cleanup(connection_manager):
    """Test proper cleanup of connection manager resources."""
    # Start the manager
    await connection_manager.start()
    assert connection_manager._health_check_task is not None

    # Close the manager
    await connection_manager.close()

    # Verify cleanup
    assert connection_manager._closing is True
    assert connection_manager._connection_pool is None
    assert len(connection_manager._channel_pools) == 0


@pytest.mark.asyncio
async def test_health_check_error_handling(connection_manager, mock_rabbitmq):
    """Test health check error handling."""
    # Configure channel to raise an error
    mock_rabbitmq["channel"].is_closed = True

    # Start health check
    await connection_manager.start()

    # Wait for health check
    await asyncio.sleep(rabbitmq_settings.monitoring_interval + 0.1)

    # Clean up
    await connection_manager.close()
