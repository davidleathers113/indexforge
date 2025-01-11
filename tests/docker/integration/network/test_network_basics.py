"""Test basic network connectivity."""

from typing import Any, Dict, Generator

import docker
import pytest

from ...utils.docker_test_utils import DockerTestUtils


@pytest.fixture
def docker_network(docker_client: Any) -> Generator[Dict[str, Any], None, None]:
    """Create a dedicated test network."""
    network = docker_client.networks.create(
        "test-network",
        driver="bridge",
        check_duplicate=True,
    )
    try:
        yield network.attrs
    finally:
        network.remove()


def test_network_creation(docker_client: Any) -> None:
    """Test network creation and removal."""
    network = docker_client.networks.create(
        "test-create-network",
        driver="bridge",
    )

    try:
        # Verify network exists
        network_info = docker_client.networks.get("test-create-network")
        assert network_info.attrs["Driver"] == "bridge"
        assert network_info.attrs["Name"] == "test-create-network"
    finally:
        network.remove()


def test_container_network_connection(docker_client: Any, docker_network: Dict[str, Any]) -> None:
    """Test container can connect to network."""
    container = docker_client.containers.run(
        "test-image:latest",
        network=docker_network["Name"],
        detach=True,
        remove=True,
    )

    try:
        # Wait for container to be ready
        DockerTestUtils.wait_for_container_health(container)

        # Verify network settings
        container.reload()
        assert docker_network["Name"] in container.attrs["NetworkSettings"]["Networks"]

        # Test network connectivity
        result = container.exec_run("ping -c 1 1.1.1.1")
        assert result.exit_code == 0, "Container has no network connectivity"
    finally:
        container.stop()
