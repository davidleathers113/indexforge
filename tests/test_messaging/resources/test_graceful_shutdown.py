"""Tests for RabbitMQ graceful shutdown scenarios."""

import asyncio

import pytest



@pytest.mark.asyncio
async def test_manager_shutdown(connection_manager, mock_rabbitmq):
    """Test graceful shutdown of connection manager.

    Verifies that:
    1. All connections are properly closed
    2. All channels are properly closed
    3. Health check is stopped
    4. Resources are released in correct order
    """
    # Track cleanup order
    cleanup_order = []

    async def tracked_connection_close():
        cleanup_order.append("connection")

    async def tracked_channel_close():
        cleanup_order.append("channel")

    mock_rabbitmq["connection"].close = tracked_connection_close
    mock_rabbitmq["channel"].close = tracked_channel_close

    # Create some active resources
    async with connection_manager.acquire_connection() as connection:
        assert connection == mock_rabbitmq["connection"]
        async with connection_manager.acquire_channel() as channel:
            assert channel == mock_rabbitmq["channel"]
            # Start health checks
            await connection_manager.start()

            # Initiate shutdown
            await connection_manager.close()

    # Verify cleanup order and completeness
    assert "channel" in cleanup_order
    assert "connection" in cleanup_order
    assert cleanup_order.index("channel") < cleanup_order.index("connection")
    assert not connection_manager._is_running


@pytest.mark.asyncio
async def test_shutdown_with_active_operations(connection_manager, mock_rabbitmq):
    """Test shutdown while operations are in progress.

    Verifies that:
    1. Active operations are allowed to complete
    2. New operations are rejected
    3. Resources are cleaned up after active operations finish
    """
    operation_completed = False

    async def long_running_operation():
        nonlocal operation_completed
        await asyncio.sleep(0.2)
        operation_completed = True

    # Start an operation
    async with connection_manager.acquire_channel() as channel:
        assert channel == mock_rabbitmq["channel"]
        # Start the long-running operation
        task = asyncio.create_task(long_running_operation())

        try:
            # Start shutdown
            await connection_manager.close()

            # Verify operation was allowed to complete
            assert operation_completed

            # Verify new operations are rejected
            with pytest.raises(RuntimeError, match="shutdown"):
                async with connection_manager.acquire_channel():
                    pass
        finally:
            await task


@pytest.mark.asyncio
async def test_shutdown_error_handling(connection_manager, mock_rabbitmq):
    """Test handling of errors during shutdown.

    Verifies that:
    1. Errors during cleanup don't prevent other cleanups
    2. All resources are attempted to be cleaned up
    3. Errors are logged but don't prevent shutdown
    """
    cleanup_attempts = []

    async def failing_connection_close():
        cleanup_attempts.append("connection")
        raise RuntimeError("Cleanup error")

    async def failing_channel_close():
        cleanup_attempts.append("channel")
        raise RuntimeError("Cleanup error")

    mock_rabbitmq["connection"].close = failing_connection_close
    mock_rabbitmq["channel"].close = failing_channel_close

    # Create some resources
    async with connection_manager.acquire_connection():
        async with connection_manager.acquire_channel():
            pass

    # Attempt shutdown
    await connection_manager.close()

    # Verify all cleanup was attempted
    assert "channel" in cleanup_attempts
    assert "connection" in cleanup_attempts
    assert not connection_manager._is_running
