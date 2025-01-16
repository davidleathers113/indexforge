"""Test container process management."""

from typing import Any

import docker

from ..config.test_config import REQUIRED_PROCESSES, SECURITY_REQUIREMENTS
from ..utils.docker_test_utils import DockerTestUtils


def test_process_hierarchy(running_container: dict[str, Any]) -> None:
    """Test that process hierarchy is correctly established."""
    result = running_container.exec_run("ps -ef --forest")
    assert result.exit_code == 0, "Failed to check process hierarchy"

    processes = result.output.decode().split("\n")

    # Verify tini is PID 1
    assert any(
        "tini" in line and "1 0" in line for line in processes
    ), "tini is not running as PID 1"

    # Verify main application is child of tini
    assert any(
        "python" in line and "─" in line for line in processes
    ), "Python process is not a child of tini"


def test_required_processes(running_container: dict[str, Any]) -> None:
    """Test that all required processes are running."""
    container_type = running_container.labels.get("container.type", "base")
    required = REQUIRED_PROCESSES[container_type]

    assert DockerTestUtils.check_process_isolation(
        running_container, required
    ), f"Not all required processes for {container_type} are running"


def test_process_user(running_container: dict[str, Any]) -> None:
    """Test that processes run as the correct user."""
    result = running_container.exec_run("ps -eo uid,cmd")
    assert result.exit_code == 0, "Failed to check process users"

    processes = result.output.decode().split("\n")

    # Check that no process runs as root (uid 0) except tini
    for process in processes:
        if not process.strip():
            continue
        uid = int(process.split()[0])
        cmd = " ".join(process.split()[1:])
        if "tini" not in cmd:
            assert uid < SECURITY_REQUIREMENTS["max_user_id"], (
                f"Process '{cmd}' running with uid {uid}, "
                f"exceeding maximum allowed {SECURITY_REQUIREMENTS['max_user_id']}"
            )
            assert uid != 0, f"Process '{cmd}' running as root"


def test_process_isolation(running_container: dict[str, Any]) -> None:
    """Test process isolation and namespace separation."""
    # Check process namespace isolation
    result = running_container.exec_run("readlink /proc/1/ns/pid")
    assert result.exit_code == 0, "Failed to check PID namespace"
    container_ns = result.output.decode().strip()

    # Verify we're in a separate namespace
    assert container_ns != "pid:[1]", "Container not running in isolated PID namespace"

    # Check process capabilities
    result = running_container.exec_run("grep CapEff /proc/1/status")
    assert result.exit_code == 0, "Failed to check process capabilities"
    capabilities = result.output.decode().strip()

    # Verify dropped capabilities
    assert "0000000000000000" in capabilities, "Container has excessive capabilities"


def test_signal_handling(docker_client: Any) -> None:
    """Test proper signal handling by processes."""
    container = docker_client.containers.run(
        "test-image:latest",
        detach=True,
        remove=True,
    )

    try:
        # Wait for container to be ready
        DockerTestUtils.wait_for_container_health(container)

        # Send SIGTERM to main process
        container.kill(signal="SIGTERM")

        # Check that processes shut down gracefully
        container.wait(timeout=10)
        container.reload()

        assert container.status == "exited", "Container did not exit gracefully"
        assert container.attrs["State"]["ExitCode"] == 0, "Container exited with non-zero code"
    except (docker.errors.APIError, docker.errors.ContainerError):
        container.remove(force=True)
        raise
