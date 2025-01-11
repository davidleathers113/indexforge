"""Test volume data persistence."""

import uuid
from typing import Any, Dict

import pytest

from ...utils.docker_test_utils import DockerTestUtils


def test_data_persistence(docker_client: Any, test_volume: Dict[str, Any]) -> None:
    """Test data persistence across container restarts."""
    test_data = "test data " + uuid.uuid4().hex
    mount_point = "/data"

    # Write data in first container
    container1 = docker_client.containers.run(
        "test-image:latest",
        command=f"sh -c 'echo {test_data} > {mount_point}/test.txt'",
        volumes={test_volume["Name"]: {"bind": mount_point, "mode": "rw"}},
        detach=True,
        remove=True,
    )

    try:
        container1.wait(timeout=10)
        assert container1.wait()["StatusCode"] == 0, "Failed to write test data"
    finally:
        container1.stop()

    # Read data in second container
    container2 = docker_client.containers.run(
        "test-image:latest",
        command=f"cat {mount_point}/test.txt",
        volumes={test_volume["Name"]: {"bind": mount_point, "mode": "ro"}},
        detach=True,
        remove=True,
    )

    try:
        result = container2.wait(timeout=10)
        assert result["StatusCode"] == 0, "Failed to read test data"

        output = container2.logs().decode().strip()
        assert output == test_data, "Data not persisted correctly"
    finally:
        container2.stop()


def test_concurrent_access(docker_client: Any, test_volume: Dict[str, Any]) -> None:
    """Test concurrent access to volume data."""
    mount_point = "/data"
    test_file = f"{mount_point}/concurrent.txt"

    # Start two containers with the same volume
    container1 = docker_client.containers.run(
        "test-image:latest",
        volumes={test_volume["Name"]: {"bind": mount_point, "mode": "rw"}},
        detach=True,
        remove=True,
    )

    container2 = docker_client.containers.run(
        "test-image:latest",
        volumes={test_volume["Name"]: {"bind": mount_point, "mode": "rw"}},
        detach=True,
        remove=True,
    )

    try:
        # Write from both containers
        container1.exec_run(f"echo 'data1' >> {test_file}")
        container2.exec_run(f"echo 'data2' >> {test_file}")

        # Verify both writes succeeded
        result = container1.exec_run(f"cat {test_file}")
        content = result.output.decode()
        assert "data1" in content and "data2" in content, "Concurrent writes failed"
    finally:
        container1.stop()
        container2.stop()
