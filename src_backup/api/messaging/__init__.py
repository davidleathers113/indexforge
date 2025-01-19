"""RabbitMQ messaging package.

This package provides a robust implementation of RabbitMQ messaging with features including:
- Connection pooling and management
- Channel management
- Message type definitions
- Configuration management
- OpenTelemetry integration
- Error handling and logging
"""

from src.api.messaging.rabbitmq_config import RabbitMQSettings, rabbitmq_settings
from src.api.messaging.rabbitmq_connection_manager import (
    RabbitMQChannelError,
    RabbitMQConnectionError,
    RabbitMQConnectionManager,
    rabbitmq_manager,
)
from src.api.messaging.rabbitmq_message_types import (
    Message,
    MessagePriority,
    MessageStatus,
    ProcessingResult,
)


__all__ = [
    # Connection Management
    "RabbitMQConnectionManager",
    "rabbitmq_manager",
    "RabbitMQConnectionError",
    "RabbitMQChannelError",
    # Configuration
    "RabbitMQSettings",
    "rabbitmq_settings",
    # Message Types
    "Message",
    "MessagePriority",
    "MessageStatus",
    "ProcessingResult",
]
