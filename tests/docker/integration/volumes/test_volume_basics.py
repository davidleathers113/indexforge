"""Test basic volume operations."""

import uuid
from typing import Any, Dict, Generator

import docker
import pytest

from ...utils.docker_test_utils import DockerTestUtils


@pytest.fixture
def test_volume(docker_client: Any) -> Generator[Dict[str, Any], None, None]:
    """Create a test volume."""
    volume = docker_client.volumes.create(
        name=f"test-volume-{uuid.uuid4().hex[:8]}",
        driver="local",
    )
    try:
        yield volume.attrs
    finally:
        volume.remove(force=True)


def test_volume_creation(docker_client: Any) -> None:
    """Test volume creation and removal."""
    volume_name = f"test-volume-{uuid.uuid4().hex[:8]}"
    volume = docker_client.volumes.create(name=volume_name)

    try:
        # Verify volume exists
        volume_info = docker_client.volumes.get(volume_name)
        assert volume_info.name == volume_name
        assert volume_info.attrs["Driver"] == "local"
    finally:
        volume.remove()


def test_volume_mounting(docker_client: Any, test_volume: Dict[str, Any]) -> None:
    """Test volume mounting in container."""
    container = docker_client.containers.run(
        "test-image:latest",
        volumes={test_volume["Name"]: {"bind": "/data", "mode": "rw"}},
        command="ls -la /data",
        detach=True,
        remove=True,
    )

    try:
        result = container.wait(timeout=10)
        assert result["StatusCode"] == 0, "Failed to list mounted volume"

        # Verify mount point exists
        output = container.logs().decode()
        assert "/data" in output, "Volume mount point not found"
    finally:
        container.stop()
