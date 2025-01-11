"""Test container port mapping and exposure."""

import socket
from typing import Any

import docker
import pytest
import requests

from ...utils.docker_test_utils import DockerTestUtils


def test_port_binding(docker_client: Any) -> None:
    """Test basic port binding functionality."""
    container = docker_client.containers.run(
        "test-image:latest",
        ports={"8000/tcp": None},  # Assign random port
        detach=True,
        remove=True,
    )

    try:
        # Wait for container to be ready
        DockerTestUtils.wait_for_container_health(container)

        # Get assigned port
        container.reload()
        port = container.ports["8000/tcp"][0]["HostPort"]

        # Test HTTP connection
        response = requests.get(f"http://localhost:{port}/health")
        assert response.status_code == 200, "Health check endpoint not accessible"
    finally:
        container.stop()


def test_multiple_ports(docker_client: Any) -> None:
    """Test binding multiple ports."""
    ports = {
        "8000/tcp": None,  # HTTP
        "8001/tcp": None,  # Metrics
    }

    container = docker_client.containers.run(
        "test-image:latest",
        ports=ports,
        detach=True,
        remove=True,
    )

    try:
        # Wait for container to be ready
        DockerTestUtils.wait_for_container_health(container)
        container.reload()

        # Test each port
        for internal_port in ports:
            host_port = container.ports[internal_port][0]["HostPort"]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("localhost", int(host_port)))
            sock.close()

            assert result == 0, f"Port {host_port} is not accessible"
    finally:
        container.stop()


def test_port_conflict_handling(docker_client: Any) -> None:
    """Test handling of port binding conflicts."""
    # Start first container with specific port
    container1 = docker_client.containers.run(
        "test-image:latest",
        ports={"8000/tcp": "8080"},
        detach=True,
        remove=True,
    )

    try:
        # Attempt to start second container with same port
        with pytest.raises(docker.errors.APIError) as exc_info:
            container2 = docker_client.containers.run(
                "test-image:latest",
                ports={"8000/tcp": "8080"},
                detach=True,
                remove=True,
            )
            container2.stop()

        assert "port is already allocated" in str(exc_info.value)
    finally:
        container1.stop()
