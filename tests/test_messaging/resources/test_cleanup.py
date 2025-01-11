"""Tests for RabbitMQ resource cleanup scenarios."""


import pytest



@pytest.mark.asyncio
async def test_connection_cleanup_after_context(connection_manager, mock_rabbitmq):
    """Test connection cleanup after context manager exit.

    Verifies that:
    1. Connection is properly closed after context exit
    2. Resources are released from the pool
    3. Cleanup callbacks are executed
    """
    # Track close calls
    close_calls = 0
    original_close = mock_rabbitmq["connection"].close

    async def tracked_close():
        nonlocal close_calls
        close_calls += 1
        await original_close()

    mock_rabbitmq["connection"].close = tracked_close

    # Use connection in context
    async with connection_manager.acquire_connection() as connection:
        assert connection == mock_rabbitmq["connection"]
        assert not connection.is_closed

    # Verify cleanup
    assert close_calls == 1
    assert connection_manager._connection_pool.empty()


@pytest.mark.asyncio
async def test_channel_cleanup_after_context(connection_manager, mock_rabbitmq):
    """Test channel cleanup after context manager exit.

    Verifies that:
    1. Channel is properly closed after context exit
    2. Resources are released from the pool
    3. Cleanup callbacks are executed
    """
    # Track close calls
    close_calls = 0
    original_close = mock_rabbitmq["channel"].close

    async def tracked_close():
        nonlocal close_calls
        close_calls += 1
        await original_close()

    mock_rabbitmq["channel"].close = tracked_close

    # Use channel in context
    async with connection_manager.acquire_channel() as channel:
        assert channel == mock_rabbitmq["channel"]
        assert not channel.is_closed

    # Verify cleanup
    assert close_calls == 1
    assert connection_manager._channel_pool.empty()


@pytest.mark.asyncio
async def test_cleanup_on_error(connection_manager, mock_rabbitmq):
    """Test resource cleanup when errors occur.

    Verifies that:
    1. Resources are cleaned up after errors
    2. Error propagation doesn't prevent cleanup
    3. All resources are properly released
    """
    # Track cleanup calls
    connection_cleanups = 0
    channel_cleanups = 0

    async def tracked_connection_close():
        nonlocal connection_cleanups
        connection_cleanups += 1

    async def tracked_channel_close():
        nonlocal channel_cleanups
        channel_cleanups += 1

    mock_rabbitmq["connection"].close = tracked_connection_close
    mock_rabbitmq["channel"].close = tracked_channel_close

    # Simulate error in connection usage
    with pytest.raises(RuntimeError):
        async with connection_manager.acquire_connection():
            raise RuntimeError("Test error")

    assert connection_cleanups == 1

    # Simulate error in channel usage
    with pytest.raises(RuntimeError):
        async with connection_manager.acquire_channel():
            raise RuntimeError("Test error")

    assert channel_cleanups == 1
