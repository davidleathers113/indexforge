"""Tests for RabbitMQ memory leak prevention scenarios."""

import gc
import weakref

import pytest

from src.api.messaging import rabbitmq_settings
from src.api.messaging.rabbitmq_connection_manager import (
    RabbitMQChannelError,
    RabbitMQConnectionError,
)


@pytest.mark.asyncio
async def test_connection_reference_cleanup(connection_manager, mock_rabbitmq):
    """Test proper cleanup of connection references.

    Verifies that:
    1. Connection objects are properly dereferenced
    2. No lingering references in the pool
    3. Garbage collection can clean up unused connections
    """
    connection_refs = []

    # Create and track weak references to connections
    for _ in range(2):
        async with connection_manager.acquire_connection() as connection:
            connection_refs.append(weakref.ref(connection))

    # Force garbage collection
    gc.collect()

    # Verify references are cleaned up
    assert all(ref() is None for ref in connection_refs)
    assert connection_manager._connection_pool.empty()


@pytest.mark.asyncio
async def test_channel_reference_cleanup(connection_manager, mock_rabbitmq):
    """Test proper cleanup of channel references.

    Verifies that:
    1. Channel objects are properly dereferenced
    2. No lingering references in the pool
    3. Garbage collection can clean up unused channels
    """
    channel_refs = []

    # Create and track weak references to channels
    for _ in range(2):
        async with connection_manager.acquire_channel() as channel:
            channel_refs.append(weakref.ref(channel))

    # Force garbage collection
    gc.collect()

    # Verify references are cleaned up
    assert all(ref() is None for ref in channel_refs)
    assert connection_manager._channel_pool.empty()


@pytest.mark.asyncio
async def test_circular_reference_prevention(connection_manager, mock_rabbitmq):
    """Test prevention of circular references.

    Verifies that:
    1. No circular references between connection and channels
    2. No circular references in error handling
    3. Resources are properly cleaned up after errors
    """
    connection_ref = None
    channel_ref = None

    # Create potentially circular reference scenario
    async with connection_manager.acquire_connection() as connection:
        connection_ref = weakref.ref(connection)

        async with connection_manager.acquire_channel() as channel:
            channel_ref = weakref.ref(channel)

            # Simulate error that might create circular reference
            try:
                raise RuntimeError("Test error")
            except RuntimeError:
                pass

    # Force garbage collection
    gc.collect()

    # Verify no lingering references
    assert connection_ref() is None
    assert channel_ref() is None
    assert connection_manager._connection_pool.empty()
    assert connection_manager._channel_pool.empty()


@pytest.mark.asyncio
async def test_resource_limit_enforcement(connection_manager, mock_rabbitmq):
    """Test enforcement of resource limits.

    Verifies that:
    1. Connection pool respects size limits
    2. Channel pool respects size limits
    3. Resources are properly released when limits are reached
    """
    # Store original pool sizes
    original_pool_size = rabbitmq_settings.pool_size
    original_max_channels = rabbitmq_settings.max_channels_per_connection

    try:
        # Set small pool sizes for testing
        rabbitmq_settings.pool_size = 2
        rabbitmq_settings.max_channels_per_connection = 2

        connections = []
        channels = []

        # Try to exceed connection pool size
        for _ in range(3):
            try:
                async with connection_manager.acquire_connection() as conn:
                    connections.append(conn)
            except RabbitMQConnectionError:
                pass

        assert len(connections) <= rabbitmq_settings.pool_size

        # Try to exceed channel pool size
        for _ in range(3):
            try:
                async with connection_manager.acquire_channel() as chan:
                    channels.append(chan)
            except RabbitMQChannelError:
                pass

        assert len(channels) <= rabbitmq_settings.max_channels_per_connection

    finally:
        # Restore original pool sizes
        rabbitmq_settings.pool_size = original_pool_size
        rabbitmq_settings.max_channels_per_connection = original_max_channels
