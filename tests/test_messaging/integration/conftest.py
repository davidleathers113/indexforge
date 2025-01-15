"""Fixtures for RabbitMQ integration tests."""

import asyncio
import socket
from typing import AsyncGenerator, Dict

import docker
from docker.models.containers import Container
import pytest
import pytest_asyncio

from src.api.messaging.rabbitmq_config import rabbitmq_settings


def is_port_available(port: int) -> bool:
    """Check if a port is available on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", port))
            return True
        except socket.error:
            return False


@pytest.fixture(scope="session")
def docker_client() -> docker.DockerClient:
    """Create a Docker client for managing containers."""
    return docker.from_env()


@pytest.fixture(scope="session")
def rabbitmq_port() -> int:
    """Get an available port for RabbitMQ."""
    # Try ports in range 5672-5699
    for port in range(5672, 5700):
        if is_port_available(port):
            return port
    raise RuntimeError("No available ports for RabbitMQ")


@pytest.fixture(scope="session")
def rabbitmq_container(docker_client: docker.DockerClient, rabbitmq_port: int) -> Container:
    """Start a RabbitMQ container for testing.

    The container uses the official RabbitMQ image with management plugin enabled.
    It is configured with:
    - Default credentials (guest/guest)
    - Management plugin enabled
    - Health check configured
    - Resource limits set
    """
    container = docker_client.containers.run(
        "rabbitmq:3.13-management",
        detach=True,
        environment={
            "RABBITMQ_DEFAULT_USER": "guest",
            "RABBITMQ_DEFAULT_PASS": "guest",
        },
        ports={"5672/tcp": rabbitmq_port, "15672/tcp": None},  # Random port for management
        healthcheck={
            "test": ["CMD", "rabbitmq-diagnostics", "check_port_connectivity"],
            "interval": 2000000000,  # 2 seconds in nanoseconds
            "timeout": 1000000000,  # 1 second in nanoseconds
            "retries": 3,
        },
        mem_limit="512m",
        cpu_count=1,
    )

    # Wait for container to be healthy
    while (
        container.status != "running" or container.attrs["State"]["Health"]["Status"] != "healthy"
    ):
        container.reload()
        asyncio.sleep(0.5)

    yield container

    # Cleanup
    container.stop()
    container.remove(force=True)


@pytest.fixture(scope="session")
def integration_settings(rabbitmq_container: Container, rabbitmq_port: int) -> Dict:
    """Configure RabbitMQ settings for integration tests."""
    # Store original settings
    original_broker_url = rabbitmq_settings.broker_url
    original_connection_name = rabbitmq_settings.connection_name

    # Update settings for integration tests
    rabbitmq_settings.broker_url = f"amqp://guest:guest@localhost:{rabbitmq_port}/"
    rabbitmq_settings.connection_name = "integration_test"

    yield {
        "broker_url": rabbitmq_settings.broker_url,
        "connection_name": rabbitmq_settings.connection_name,
    }

    # Restore original settings
    rabbitmq_settings.broker_url = original_broker_url
    rabbitmq_settings.connection_name = original_connection_name


@pytest_asyncio.fixture(scope="function")
async def integration_connection_manager(integration_settings: Dict) -> AsyncGenerator:
    """Create a RabbitMQConnectionManager instance for integration tests."""
    from src.api.messaging.rabbitmq_connection_manager import RabbitMQConnectionManager

    manager = RabbitMQConnectionManager()
    await manager.start()

    yield manager

    await manager.close()
