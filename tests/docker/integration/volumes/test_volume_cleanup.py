"""Test volume cleanup and lifecycle management."""

from typing import Any, Dict

import docker
import pytest

from ...utils.docker_test_utils import DockerTestUtils


def test_anonymous_volume_cleanup(docker_client: Any) -> None:
    """Test cleanup of anonymous volumes."""
    container = docker_client.containers.run(
        "test-image:latest",
        volumes=["/data"],  # Anonymous volume
        detach=True,
        remove=True,
    )

    try:
        # Get volume information
        container.reload()
        mounts = container.attrs["Mounts"]
        assert len(mounts) > 0, "No volumes mounted"

        volume_name = mounts[0]["Name"]

        # Stop container and verify volume is removed
        container.stop()
        container.wait()

        with pytest.raises(docker.errors.NotFound):
            docker_client.volumes.get(volume_name)
    except (docker.errors.APIError, docker.errors.NotFound):
        if container:
            container.remove(force=True)


def test_named_volume_persistence(docker_client: Any) -> None:
    """Test that named volumes persist after container removal."""
    volume = docker_client.volumes.create(name="test-persist")

    try:
        # Create and remove container
        container = docker_client.containers.run(
            "test-image:latest",
            volumes={"test-persist": {"bind": "/data", "mode": "rw"}},
            detach=True,
            remove=True,
        )

        try:
            container.wait(timeout=10)
        finally:
            container.stop()

        # Verify volume still exists
        volume_info = docker_client.volumes.get("test-persist")
        assert volume_info.name == "test-persist"
    finally:
        volume.remove()


def test_volume_removal_with_content(docker_client: Any) -> None:
    """Test volume removal with existing content."""
    volume = docker_client.volumes.create(name="test-content")

    try:
        # Create content in volume
        container = docker_client.containers.run(
            "test-image:latest",
            command="touch /data/test.txt",
            volumes={"test-content": {"bind": "/data", "mode": "rw"}},
            detach=True,
            remove=True,
        )

        try:
            container.wait(timeout=10)
        finally:
            container.stop()

        # Force remove volume
        volume.remove(force=True)

        # Verify volume is gone
        with pytest.raises(docker.errors.NotFound):
            docker_client.volumes.get("test-content")
    except (docker.errors.APIError, docker.errors.NotFound):
        volume.remove(force=True)
