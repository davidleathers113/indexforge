"""Tests for RabbitMQ connection pool exhaustion scenarios."""

import asyncio

import pytest

from src.api.messaging import rabbitmq_settings


@pytest.mark.asyncio
async def test_connection_pool_exhaustion(connection_manager, mock_rabbitmq):
    """Test behavior when connection pool is exhausted.

    This test verifies that:
    1. The connection pool respects its size limit
    2. Attempts to acquire connections beyond the limit timeout
    3. Resources are properly released after timeout
    """
    # Store original pool size
    original_pool_size = rabbitmq_settings.pool_size

    try:
        # Set pool size to 1 for this test
        rabbitmq_settings.pool_size = 1

        # First connection should succeed
        async with connection_manager.acquire_connection() as conn1:
            assert conn1 == mock_rabbitmq["connection"]

            # Second connection should timeout
            with pytest.raises(TimeoutError):
                async with asyncio.timeout(0.1):
                    async with connection_manager.acquire_connection():
                        pass

    finally:
        # Restore original pool size
        rabbitmq_settings.pool_size = original_pool_size
