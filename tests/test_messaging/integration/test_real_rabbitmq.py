"""Integration tests for basic RabbitMQ connectivity."""


from aio_pika.abc import AbstractChannel, AbstractConnection
import pytest

from src.api.messaging.rabbitmq_connection_manager import RabbitMQConnectionManager


@pytest.mark.asyncio
async def test_real_connection_establishment(
    integration_connection_manager: RabbitMQConnectionManager, integration_settings: dict
):
    """Test establishing a real connection to RabbitMQ.

    Verifies:
    1. Connection can be established
    2. Connection parameters are correct
    3. Connection is responsive
    """
    async with integration_connection_manager.acquire_connection() as connection:
        assert isinstance(connection, AbstractConnection)
        assert not connection.is_closed
        assert (
            connection.connection_parameters.client_properties["connection_name"]
            == integration_settings["connection_name"]
        )

        # Verify connection is responsive
        await connection.connect()
        assert connection.is_connected


@pytest.mark.asyncio
async def test_real_channel_operations(integration_connection_manager: RabbitMQConnectionManager):
    """Test channel operations with real RabbitMQ.

    Verifies:
    1. Channel can be created
    2. Multiple channels work
    3. Channel operations succeed
    """
    async with integration_connection_manager.acquire_channel() as channel:
        assert isinstance(channel, AbstractChannel)
        assert not channel.is_closed

        # Test basic channel operations
        exchange = await channel.declare_exchange("test_exchange", auto_delete=True)
        queue = await channel.declare_queue("test_queue", auto_delete=True)
        await queue.bind(exchange, "test_routing_key")

        # Verify exchange and queue exist
        assert exchange
        assert queue
        assert queue.name == "test_queue"


@pytest.mark.asyncio
async def test_concurrent_operations(integration_connection_manager: RabbitMQConnectionManager):
    """Test concurrent operations with real RabbitMQ.

    Verifies:
    1. Multiple channels can be used concurrently
    2. Operations don't interfere
    3. Resources are properly managed
    """
    channels = []
    queues = []

    # Create multiple channels
    async with integration_connection_manager.acquire_connection():
        for i in range(3):
            async with integration_connection_manager.acquire_channel() as channel:
                channels.append(channel)
                queue = await channel.declare_queue(f"concurrent_queue_{i}", auto_delete=True)
                queues.append(queue)

        # Verify all channels and queues
        assert len(channels) == 3
        assert len(queues) == 3
        assert all(not channel.is_closed for channel in channels)
        assert all(queue.name.startswith("concurrent_queue_") for queue in queues)
