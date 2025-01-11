"""Test network isolation between containers."""

from typing import Any, Dict

import docker
import pytest

from ...utils.docker_test_utils import DockerTestUtils


def test_network_separation(docker_client: Any, docker_network: Dict[str, Any]) -> None:
    """Test containers in different networks cannot communicate."""
    # Start container in test network
    container1 = docker_client.containers.run(
        "test-image:latest",
        name="test-container1",
        network=docker_network["Name"],
        detach=True,
        remove=True,
    )

    # Start container in default network
    container2 = docker_client.containers.run(
        "test-image:latest",
        name="test-container2",
        detach=True,
        remove=True,
    )

    try:
        # Wait for containers
        DockerTestUtils.wait_for_container_health(container1)
        DockerTestUtils.wait_for_container_health(container2)

        # Container2 should not be able to reach container1
        result = container2.exec_run("ping -c 1 test-container1")
        assert result.exit_code != 0, "Container in different network should not be reachable"
    finally:
        container1.stop()
        container2.stop()


def test_network_policy(docker_client: Any, docker_network: Dict[str, Any]) -> None:
    """Test network policy enforcement."""
    # Create network with internal flag
    internal_network = docker_client.networks.create(
        "test-internal",
        driver="bridge",
        internal=True,
    )

    try:
        # Start container in internal network
        container = docker_client.containers.run(
            "test-image:latest",
            network=internal_network.name,
            detach=True,
            remove=True,
        )

        try:
            # Wait for container
            DockerTestUtils.wait_for_container_health(container)

            # Should not be able to reach internet
            result = container.exec_run("ping -c 1 8.8.8.8")
            assert result.exit_code != 0, "Internal network should not have internet access"
        finally:
            container.stop()
    finally:
        internal_network.remove()


def test_host_network_isolation(docker_client: Any) -> None:
    """Test isolation from host network."""
    container = docker_client.containers.run(
        "test-image:latest",
        detach=True,
        remove=True,
    )

    try:
        # Wait for container
        DockerTestUtils.wait_for_container_health(container)

        # Should not be able to access host network services
        result = container.exec_run("nc -z host.docker.internal 22")
        assert result.exit_code != 0, "Container should not access host SSH port"
    finally:
        container.stop()
