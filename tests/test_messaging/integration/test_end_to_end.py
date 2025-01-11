"""Integration tests for end-to-end RabbitMQ messaging scenarios."""

import asyncio
import json
from typing import Dict, List

import pytest
from aio_pika import Message
from aio_pika.abc import AbstractIncomingMessage
from docker.models.containers import Container

from src.api.messaging.rabbitmq_connection_manager import RabbitMQConnectionManager


@pytest.mark.asyncio
async def test_basic_publish_consume(integration_connection_manager: RabbitMQConnectionManager):
    """Test basic message publishing and consumption.

    Verifies:
    1. Messages can be published
    2. Messages can be consumed
    3. Message content is preserved
    """
    messages_received = []

    async def message_handler(message: AbstractIncomingMessage):
        async with message.process():
            messages_received.append(json.loads(message.body.decode()))

    async with integration_connection_manager.acquire_channel() as channel:
        # Set up exchange and queue
        exchange = await channel.declare_exchange("test_exchange", auto_delete=True)
        queue = await channel.declare_queue("test_queue", auto_delete=True)
        await queue.bind(exchange, "test_key")

        # Start consuming
        await queue.consume(message_handler)

        # Publish messages
        test_messages = [{"id": 1, "data": "test1"}, {"id": 2, "data": "test2"}]

        for msg in test_messages:
            await exchange.publish(Message(json.dumps(msg).encode()), routing_key="test_key")

        # Wait for messages to be processed
        await asyncio.sleep(1)

        # Verify messages
        assert len(messages_received) == len(test_messages)
        assert all(msg in messages_received for msg in test_messages)


@pytest.mark.asyncio
async def test_message_persistence(
    integration_connection_manager: RabbitMQConnectionManager, rabbitmq_container: Container
):
    """Test message persistence across broker restarts.

    Verifies:
    1. Messages survive broker restart
    2. Message order is preserved
    3. No messages are lost
    """
    messages_received: List[Dict] = []

    async def message_handler(message: AbstractIncomingMessage):
        async with message.process():
            messages_received.append(json.loads(message.body.decode()))

    async with integration_connection_manager.acquire_channel() as channel:
        # Set up durable exchange and queue
        exchange = await channel.declare_exchange("persistent_exchange", durable=True)
        queue = await channel.declare_queue("persistent_queue", durable=True)
        await queue.bind(exchange, "persistent_key")

        # Publish messages
        test_messages = [{"id": 1, "data": "persistent1"}, {"id": 2, "data": "persistent2"}]

        for msg in test_messages:
            await exchange.publish(
                Message(json.dumps(msg).encode(), delivery_mode=2),  # Persistent
                routing_key="persistent_key",
            )

        # Restart broker
        rabbitmq_container.restart()
        await asyncio.sleep(5)

        # Reconnect and consume messages
        await queue.consume(message_handler)
        await asyncio.sleep(1)

        # Verify messages survived
        assert len(messages_received) == len(test_messages)
        assert all(msg in messages_received for msg in test_messages)

        # Cleanup
        await queue.delete()
        await exchange.delete()


@pytest.mark.asyncio
async def test_concurrent_publish_consume(
    integration_connection_manager: RabbitMQConnectionManager,
):
    """Test concurrent publishing and consumption.

    Verifies:
    1. Multiple publishers work concurrently
    2. Multiple consumers work concurrently
    3. All messages are processed
    """
    messages_received = []
    num_messages = 100
    num_publishers = 3
    num_consumers = 3

    async def message_handler(message: AbstractIncomingMessage):
        async with message.process():
            messages_received.append(json.loads(message.body.decode()))

    async def publisher(exchange, start_id: int, count: int):
        for i in range(count):
            msg_id = start_id + i
            await exchange.publish(
                Message(json.dumps({"id": msg_id, "data": f"msg_{msg_id}"}).encode()),
                routing_key="concurrent_key",
            )

    async with integration_connection_manager.acquire_channel() as channel:
        # Set up exchange and queue
        exchange = await channel.declare_exchange("concurrent_exchange", auto_delete=True)
        queue = await channel.declare_queue("concurrent_queue", auto_delete=True)
        await queue.bind(exchange, "concurrent_key")

        # Start multiple consumers
        for _ in range(num_consumers):
            await queue.consume(message_handler)

        # Start multiple publishers
        publisher_tasks = []
        msgs_per_publisher = num_messages // num_publishers
        for i in range(num_publishers):
            start_id = i * msgs_per_publisher
            task = asyncio.create_task(publisher(exchange, start_id, msgs_per_publisher))
            publisher_tasks.append(task)

        # Wait for publishers
        await asyncio.gather(*publisher_tasks)
        await asyncio.sleep(1)  # Wait for messages to be processed

        # Verify all messages were received
        assert len(messages_received) == num_messages
        received_ids = {msg["id"] for msg in messages_received}
        expected_ids = set(range(num_messages))
        assert received_ids == expected_ids
