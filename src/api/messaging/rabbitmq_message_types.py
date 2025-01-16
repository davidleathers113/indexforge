"""RabbitMQ message type definitions.

This module defines the message structures and serialization patterns
for RabbitMQ async message communication in the application.
Includes base message types, priorities, statuses, and processing results.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MessagePriority(int, Enum):
    """Message priority levels for RabbitMQ messages."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class MessageStatus(str, Enum):
    """Status of RabbitMQ message processing."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


T = TypeVar("T")


class Message(BaseModel, Generic[T]):
    """Base message structure for all RabbitMQ communications."""

    message_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    priority: MessagePriority = Field(default=MessagePriority.NORMAL)
    correlation_id: str | None = None
    reply_to: str | None = None
    content_type: str = "application/json"
    headers: dict[str, Any] = Field(default_factory=dict)
    payload: T

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat(), UUID: lambda v: str(v)}


class ErrorDetail(BaseModel):
    """Error details for failed RabbitMQ message processing."""

    error_type: str
    error_message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    traceback: str | None = None


class ProcessingResult(BaseModel, Generic[T]):
    """Result of RabbitMQ message processing."""

    message_id: UUID
    status: MessageStatus
    result: T | None = None
    error: ErrorDetail | None = None
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
