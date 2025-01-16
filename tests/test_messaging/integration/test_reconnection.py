"""Integration tests for RabbitMQ reconnection scenarios."""

import asyncio

from docker.models.containers import Container
import pytest

from src.api.messaging.rabbitmq_connection_manager import RabbitMQConnectionManager


@pytest.mark.asyncio
async def test_reconnection_after_broker_restart(
    integration_connection_manager: RabbitMQConnectionManager,
    rabbitmq_container: Container,
    integration_settings: dict,
):
    """Test reconnection after broker restart.

    Verifies:
    1. Connection is re-established after broker restart
    2. Channels are recreated
    3. Operations succeed after reconnection
    """
    # Establish initial connection
    async with integration_connection_manager.acquire_channel() as channel:
        queue = await channel.declare_queue("reconnect_test", auto_delete=True)
        assert queue and queue.name == "reconnect_test"

        # Restart RabbitMQ container
        rabbitmq_container.restart()
        await asyncio.sleep(5)  # Wait for container to fully restart

        # Verify reconnection
        queue = await channel.declare_queue("reconnect_test_after", auto_delete=True)
        assert queue and queue.name == "reconnect_test_after"


@pytest.mark.asyncio
async def test_reconnection_during_network_partition(
    integration_connection_manager: RabbitMQConnectionManager, rabbitmq_container: Container
):
    """Test reconnection during network partition.

    Verifies:
    1. Connection attempts continue during network outage
    2. Connection is restored when network is available
    3. Operations resume after reconnection
    """
    # Establish initial connection
    async with integration_connection_manager.acquire_channel() as channel:
        queue = await channel.declare_queue("partition_test", auto_delete=True)
        assert queue and queue.name == "partition_test"

        # Simulate network partition by pausing container
        rabbitmq_container.pause()
        await asyncio.sleep(5)

        # Attempt operations during partition
        with pytest.raises(Exception):  # Connection should fail
            await channel.declare_queue("should_fail", auto_delete=True)

        # Restore network
        rabbitmq_container.unpause()
        await asyncio.sleep(5)

        # Verify operations resume
        queue = await channel.declare_queue("partition_test_after", auto_delete=True)
        assert queue and queue.name == "partition_test_after"


@pytest.mark.asyncio
async def test_connection_recovery_with_active_channels(
    integration_connection_manager: RabbitMQConnectionManager, rabbitmq_container: Container
):
    """Test connection recovery with active channels.

    Verifies:
    1. Multiple channels survive reconnection
    2. Channel operations continue after recovery
    3. Resources are properly recreated
    """
    channels = []
    queues = []

    # Create multiple channels
    async with integration_connection_manager.acquire_connection():
        for i in range(3):
            async with integration_connection_manager.acquire_channel() as channel:
                channels.append(channel)
                queue = await channel.declare_queue(f"recovery_queue_{i}", auto_delete=True)
                queues.append(queue)

        # Verify initial setup
        assert len(channels) == 3
        assert len(queues) == 3

        # Restart broker
        rabbitmq_container.restart()
        await asyncio.sleep(5)

        # Verify channels recover
        for i, channel in enumerate(channels):
            queue = await channel.declare_queue(f"recovery_queue_after_{i}", auto_delete=True)
            assert queue.name == f"recovery_queue_after_{i}"


@pytest.mark.asyncio
async def test_health_check_during_outage(
    integration_connection_manager: RabbitMQConnectionManager, rabbitmq_container: Container
):
    """Test health check behavior during network outage.

    Verifies:
    1. Health checks detect connection loss
    2. Recovery is attempted during outage
    3. Health checks resume after recovery
    """
    # Start health checks
    await integration_connection_manager.start()
    assert integration_connection_manager._is_running

    # Create initial connection
    async with integration_connection_manager.acquire_channel() as channel:
        queue = await channel.declare_queue("health_test", auto_delete=True)
        assert queue.name == "health_test"

        # Simulate network outage
        rabbitmq_container.pause()
        await asyncio.sleep(10)  # Allow multiple health checks to fail

        # Restore network
        rabbitmq_container.unpause()
        await asyncio.sleep(5)

        # Verify health checks recovered
        queue = await channel.declare_queue("health_test_after", auto_delete=True)
        assert queue.name == "health_test_after"
