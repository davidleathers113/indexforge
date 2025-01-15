"""Test volume security and permissions."""

from typing import Any, Dict

from ...utils.docker_test_utils import DockerTestUtils


def test_volume_permissions(docker_client: Any, test_volume: Dict[str, Any]) -> None:
    """Test volume mount permissions."""
    mount_point = "/data"

    container = docker_client.containers.run(
        "test-image:latest",
        volumes={test_volume["Name"]: {"bind": mount_point, "mode": "rw"}},
        user="1000:1000",  # Non-root user
        detach=True,
        remove=True,
    )

    try:
        # Wait for container to be ready
        DockerTestUtils.wait_for_container_health(container)

        # Test write permission
        result = container.exec_run(f"touch {mount_point}/test.txt")
        assert result.exit_code == 0, "Failed to write to volume as non-root user"

        # Check file ownership
        result = container.exec_run(f"stat -c '%u:%g' {mount_point}/test.txt")
        assert result.exit_code == 0, "Failed to check file ownership"
        assert result.output.decode().strip() == "1000:1000", "Incorrect file ownership"
    finally:
        container.stop()


def test_readonly_mount(docker_client: Any, test_volume: Dict[str, Any]) -> None:
    """Test read-only volume mount."""
    mount_point = "/data"

    container = docker_client.containers.run(
        "test-image:latest",
        volumes={test_volume["Name"]: {"bind": mount_point, "mode": "ro"}},
        detach=True,
        remove=True,
    )

    try:
        # Wait for container to be ready
        DockerTestUtils.wait_for_container_health(container)

        # Attempt write to read-only volume
        result = container.exec_run(f"touch {mount_point}/test.txt")
        assert result.exit_code != 0, "Write to read-only volume should fail"
    finally:
        container.stop()


def test_volume_isolation(docker_client: Any, test_volume: Dict[str, Any]) -> None:
    """Test volume mount isolation."""
    container = docker_client.containers.run(
        "test-image:latest",
        volumes={test_volume["Name"]: {"bind": "/isolated", "mode": "rw"}},
        detach=True,
        remove=True,
    )

    try:
        # Wait for container to be ready
        DockerTestUtils.wait_for_container_health(container)

        # Verify container cannot access host files
        result = container.exec_run("ls /proc/1/root")
        assert result.exit_code != 0, "Container should not access host root"

        # Verify container cannot escape mount namespace
        result = container.exec_run("mount | grep -v /isolated")
        assert "/isolated" in result.output.decode(), "Volume not properly isolated"
    finally:
        container.stop()
