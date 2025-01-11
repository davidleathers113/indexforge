# Phase 4: Event-Driven Architecture Implementation

## Overview

The Event-Driven Architecture implementation in IndexForge utilizes RabbitMQ as the message broker, providing robust asynchronous communication between microservices. This document outlines the current implementation, components, and best practices.

## Table of Contents

1. [Infrastructure](#infrastructure)
2. [Core Components](#core-components)
3. [Message Types](#message-types)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Monitoring](#monitoring)
7. [Best Practices](#best-practices)

## Infrastructure

### RabbitMQ Service Configuration

```yaml
# docker-compose.yml
rabbitmq:
  image: rabbitmq:3.13-management
  environment:
    - RABBITMQ_DEFAULT_USER=${RABBITMQ_USER:-admin}
    - RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASSWORD:-admin_password}
    - RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS=-rabbit disk_free_limit "2GB"
  ports:
    - "5672:5672" # AMQP protocol
    - "15672:15672" # Management UI
  volumes:
    - rabbitmq_data:/var/lib/rabbitmq
  healthcheck:
    test: ["CMD", "rabbitmq-diagnostics", "check_port_connectivity"]
    interval: 10s
    timeout: 5s
    retries: 3
  deploy:
    resources:
      limits:
        cpus: "1"
        memory: 2G
      reservations:
        memory: 1G
```

### Key Features

- Management UI for monitoring and administration
- Persistent storage with volume mounting
- Health checks for reliability
- Resource limits for stability
- Environment variable configuration

## Core Components

### Connection Manager

The `RabbitMQConnectionManager` provides robust connection handling:

```python
class RabbitMQConnectionManager:
    """Manages RabbitMQ connections and channels with connection pooling."""

    # Key Features:
    # - Connection pooling
    # - Automatic reconnection
    # - Health monitoring
    # - Channel management
    # - OpenTelemetry integration
    # - Error handling and logging
```

### Key Capabilities

1. **Connection Pooling**

   - Efficient connection reuse
   - Configurable pool size
   - Automatic connection lifecycle management

2. **Channel Management**

   - Channel pooling per connection
   - Automatic channel recovery
   - Resource cleanup

3. **Health Monitoring**
   - Periodic health checks
   - Connection status monitoring
   - Automatic recovery mechanisms

## Message Types

### Base Message Structure

```python
class Message(BaseModel, Generic[T]):
    """Base message structure for all RabbitMQ communications."""

    message_id: UUID
    timestamp: datetime
    priority: MessagePriority
    correlation_id: Optional[str]
    reply_to: Optional[str]
    content_type: str
    headers: Dict[str, Any]
    payload: T
```

### Message Priority Levels

```python
class MessagePriority(int, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3
```

### Processing States

```python
class MessageStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
```

## Configuration

### RabbitMQ Settings

```python
class RabbitMQSettings(BaseSettings):
    """RabbitMQ connection and operational settings."""

    # Connection settings
    broker_url: AmqpDsn
    connection_name: str

    # Pool settings
    pool_size: int
    max_channels_per_connection: int

    # Channel settings
    channel_max_size: int
    publisher_confirms: bool

    # Consumer settings
    prefetch_count: int
    consumer_timeout: float

    # Retry settings
    max_retries: int
    retry_delay: float
```

## Testing

### Test Coverage Areas

1. **Integration Tests**

   - Connection establishment
   - Channel operations
   - Message persistence
   - Concurrent operations

2. **End-to-End Tests**

   - Message publishing and consumption
   - Message persistence across restarts
   - Concurrent publishing and consuming

3. **Reconnection Tests**
   - Connection recovery
   - Channel recovery
   - Resource recreation

### Example Test Cases

```python
async def test_message_persistence():
    """Test message persistence across broker restarts."""
    # Ensures messages survive broker restarts
    # Verifies message order preservation
    # Checks for no message loss

async def test_concurrent_operations():
    """Test concurrent operations with real RabbitMQ."""
    # Verifies multiple channel usage
    # Checks operation isolation
    # Ensures proper resource management
```

## Monitoring

### Health Checks

```python
async def _health_check(self) -> None:
    """Perform periodic health checks on connections."""
    # Features:
    # - Regular connection verification
    # - Performance metrics collection
    # - Error tracking and reporting
    # - OpenTelemetry integration
```

### Metrics Collection

- Connection status
- Channel utilization
- Message throughput
- Error rates
- Processing times

## Best Practices

### Connection Management

1. Use connection pooling for efficiency
2. Implement automatic reconnection
3. Monitor connection health
4. Clean up resources properly

### Message Handling

1. Use message acknowledgments
2. Implement retry mechanisms
3. Handle errors gracefully
4. Maintain message persistence

### Security

1. Use secure credentials
2. Implement proper access control
3. Monitor for suspicious activity
4. Regular security audits

### Performance

1. Configure appropriate resource limits
2. Monitor system metrics
3. Implement proper error handling
4. Use connection and channel pooling

## Conclusion

The Event-Driven Architecture implementation provides a robust foundation for asynchronous communication between services. The implementation follows best practices for reliability, scalability, and maintainability.
