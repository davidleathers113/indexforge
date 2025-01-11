"""Test configuration and shared fixtures for RabbitMQ tests."""

import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from pytest_asyncio import fixture

from src.api.messaging.rabbitmq_config import rabbitmq_settings
from src.api.messaging.rabbitmq_connection_manager import RabbitMQConnectionManager


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@fixture
async def mock_rabbitmq():
    """Provide a mock RabbitMQ connection for testing."""
    # Create mock objects
    mock_channel = AsyncMock()
    mock_channel.is_closed = False
    mock_channel.set_qos = AsyncMock()

    mock_connection = AsyncMock()
    mock_connection.channel = AsyncMock(return_value=mock_channel)
    mock_connection.is_closed = False
    mock_connection.close = AsyncMock()

    # Mock the connection creation
    with patch("aio_pika.connect_robust", AsyncMock(return_value=mock_connection)) as mock_connect:
        yield {
            "connect": mock_connect,
            "connection": mock_connection,
            "channel": mock_channel,
        }


@pytest.fixture
def test_rabbitmq_settings():
    """Provide test settings for RabbitMQ."""
    # Store original settings
    original = {
        "broker_url": rabbitmq_settings.broker_url,
        "pool_size": rabbitmq_settings.pool_size,
        "monitoring_interval": rabbitmq_settings.monitoring_interval,
        "prefetch_count": rabbitmq_settings.prefetch_count,
    }

    # Set test values
    rabbitmq_settings.broker_url = "amqp://guest:guest@localhost:5672/test"
    rabbitmq_settings.pool_size = 2
    rabbitmq_settings.monitoring_interval = 1.0
    rabbitmq_settings.prefetch_count = 10

    yield rabbitmq_settings

    # Restore original settings
    for key, value in original.items():
        setattr(rabbitmq_settings, key, value)


@fixture
async def connection_manager(test_rabbitmq_settings) -> RabbitMQConnectionManager:
    """Provide a RabbitMQ connection manager for testing."""
    manager = RabbitMQConnectionManager()
    try:
        yield manager
    finally:
        await manager.close()
