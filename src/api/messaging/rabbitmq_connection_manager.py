"""RabbitMQ connection management.

This module provides a robust connection manager for RabbitMQ with features including:
- Connection pooling
- Automatic reconnection
- Health checks
- Channel management
- OpenTelemetry integration
- Error handling and logging
"""

import asyncio
from contextlib import asynccontextmanager
import logging
import time
from typing import AsyncGenerator, Dict, Optional
from uuid import uuid4

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractConnection
from aio_pika.pool import Pool
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from src.api.messaging.rabbitmq_config import rabbitmq_settings
from src.api.monitoring.metrics import record_error

# Configure module logger
logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class RabbitMQConnectionError(Exception):
    """Custom exception for RabbitMQ connection errors."""

    pass


class RabbitMQChannelError(Exception):
    """Custom exception for RabbitMQ channel errors."""

    pass


class RabbitMQConnectionManager:
    """Manages RabbitMQ connections and channels with connection pooling."""

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._connection_pool: Optional[Pool[AbstractConnection]] = None
        self._channel_pools: Dict[str, Pool[AbstractChannel]] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._closing = False
        self._connection_attempts = 0
        self._last_connection_error: Optional[Exception] = None
        logger.info("Initialized RabbitMQ connection manager")

    async def _create_connection(self) -> AbstractConnection:
        """Create a new RabbitMQ connection with retry logic.

        Returns:
            AbstractConnection: A new RabbitMQ connection.

        Raises:
            RabbitMQConnectionError: If connection creation fails after retries.
        """
        with tracer.start_as_current_span("rabbitmq_create_connection") as span:
            connection_id = str(uuid4())
            span.set_attribute("rabbitmq.connection_id", connection_id)
            span.set_attribute("rabbitmq.broker_url", str(rabbitmq_settings.broker_url))

            try:
                self._connection_attempts += 1
                start_time = time.monotonic()

                connection = await aio_pika.connect_robust(
                    **rabbitmq_settings.get_connection_parameters()
                )

                connection_time = time.monotonic() - start_time
                span.set_attribute("rabbitmq.connection_time", connection_time)
                logger.info(
                    "Created new RabbitMQ connection",
                    extra={
                        "connection_id": connection_id,
                        "attempt": self._connection_attempts,
                        "connection_time": connection_time,
                    },
                )
                return connection

            except Exception as e:
                self._last_connection_error = e
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(e)
                logger.error(
                    "Failed to create RabbitMQ connection",
                    extra={
                        "connection_id": connection_id,
                        "attempt": self._connection_attempts,
                        "error": str(e),
                    },
                    exc_info=True,
                )
                record_error(
                    "rabbitmq_connection_error",
                    str(e),
                    {"connection_id": connection_id, "attempt": self._connection_attempts},
                )
                raise RabbitMQConnectionError(f"Connection failed: {e}") from e

    async def _create_channel(self, connection: AbstractConnection) -> AbstractChannel:
        """Create a new channel on the given connection.

        Args:
            connection: The RabbitMQ connection to create a channel on.

        Returns:
            AbstractChannel: A new channel.

        Raises:
            RabbitMQChannelError: If channel creation fails.
        """
        with tracer.start_as_current_span("rabbitmq_create_channel") as span:
            channel_id = str(uuid4())
            span.set_attribute("rabbitmq.channel_id", channel_id)

            try:
                start_time = time.monotonic()
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=rabbitmq_settings.prefetch_count)

                channel_time = time.monotonic() - start_time
                span.set_attribute("rabbitmq.channel_time", channel_time)
                logger.debug(
                    "Created new RabbitMQ channel",
                    extra={
                        "channel_id": channel_id,
                        "prefetch_count": rabbitmq_settings.prefetch_count,
                        "channel_time": channel_time,
                    },
                )
                return channel

            except Exception as e:
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(e)
                logger.error(
                    "Failed to create RabbitMQ channel",
                    extra={
                        "channel_id": channel_id,
                        "error": str(e),
                    },
                    exc_info=True,
                )
                record_error("rabbitmq_channel_error", str(e), {"channel_id": channel_id})
                raise RabbitMQChannelError(f"Channel creation failed: {e}") from e

    @asynccontextmanager
    async def acquire_connection(self) -> AsyncGenerator[AbstractConnection, None]:
        """Acquire a connection from the pool.

        Yields:
            AbstractConnection: A RabbitMQ connection from the pool.

        Raises:
            RabbitMQConnectionError: If connection acquisition fails.
        """
        if not self._connection_pool:
            logger.debug(
                "Initializing connection pool", extra={"pool_size": rabbitmq_settings.pool_size}
            )
            self._connection_pool = Pool(
                self._create_connection,
                max_size=rabbitmq_settings.pool_size,
                loop=asyncio.get_event_loop(),
            )

        try:
            async with self._connection_pool.acquire() as connection:
                yield connection
        except Exception as e:
            logger.error("Failed to acquire connection from pool", exc_info=True)
            raise RabbitMQConnectionError(f"Failed to acquire connection: {e}") from e

    @asynccontextmanager
    async def acquire_channel(self) -> AsyncGenerator[AbstractChannel, None]:
        """Acquire a channel from the pool.

        Yields:
            AbstractChannel: A RabbitMQ channel from the pool.

        Raises:
            RabbitMQChannelError: If channel acquisition fails.
        """
        try:
            async with self.acquire_connection() as connection:
                connection_id = str(id(connection))
                if connection_id not in self._channel_pools:
                    logger.debug(
                        "Creating channel pool for connection",
                        extra={
                            "connection_id": connection_id,
                            "max_channels": rabbitmq_settings.max_channels_per_connection,
                        },
                    )
                    self._channel_pools[connection_id] = Pool(
                        lambda: self._create_channel(connection),
                        max_size=rabbitmq_settings.max_channels_per_connection,
                        loop=asyncio.get_event_loop(),
                    )

                async with self._channel_pools[connection_id].acquire() as channel:
                    yield channel
        except Exception as e:
            logger.error("Failed to acquire channel", exc_info=True)
            raise RabbitMQChannelError(f"Failed to acquire channel: {e}") from e

    async def _health_check(self) -> None:
        """Perform periodic health checks on connections."""
        while not self._closing:
            with tracer.start_as_current_span("rabbitmq_health_check") as span:
                try:
                    start_time = time.monotonic()
                    async with self.acquire_channel() as channel:
                        if not channel.is_closed:
                            check_time = time.monotonic() - start_time
                            span.set_attribute("rabbitmq.health_check_time", check_time)
                            logger.debug(
                                "RabbitMQ health check passed", extra={"check_time": check_time}
                            )
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR))
                    span.record_exception(e)
                    logger.error(
                        "RabbitMQ health check failed", extra={"error": str(e)}, exc_info=True
                    )
                    record_error("rabbitmq_health_check_error", str(e))

            await asyncio.sleep(rabbitmq_settings.monitoring_interval)

    async def start(self) -> None:
        """Start the connection manager and health checks."""
        logger.info("Starting RabbitMQ connection manager")
        self._closing = False
        self._health_check_task = asyncio.create_task(self._health_check())
        logger.info("RabbitMQ connection manager started successfully")

    async def close(self) -> None:
        """Close all connections and channels."""
        logger.info("Shutting down RabbitMQ connection manager")
        self._closing = True

        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Close all channel pools
        for pool in self._channel_pools.values():
            await pool.close()
        self._channel_pools.clear()

        # Close connection pool
        if self._connection_pool:
            await self._connection_pool.close()
            self._connection_pool = None

        logger.info(
            "RabbitMQ connection manager closed",
            extra={
                "total_connection_attempts": self._connection_attempts,
                "last_error": (
                    str(self._last_connection_error) if self._last_connection_error else None
                ),
            },
        )


# Global instance
rabbitmq_manager = RabbitMQConnectionManager()
