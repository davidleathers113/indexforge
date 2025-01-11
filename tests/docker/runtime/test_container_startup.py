"""Test container startup behavior."""

import time
from typing import Any, Dict

import docker
import pytest

from ..config.test_config import PERFORMANCE_THRESHOLDS, TEST_TIMEOUTS
from ..utils.docker_test_utils import DockerTestUtils


def test_container_starts_successfully(
    docker_client: Any, running_container: Dict[str, Any]
) -> None:
    """Test that container starts without errors."""
    assert running_container.status == "running", "Container failed to start"

    # Check container logs for startup errors
    logs = running_container.logs().decode()
    assert not any(
        error in logs.lower() for error in ["error:", "fatal:", "panic:"]
    ), "Found errors in container startup logs"


@pytest.mark.timeout(TEST_TIMEOUTS["startup"])
def test_startup_time(docker_client: Any) -> None:
    """Test that container starts within expected time."""
    start_time = time.time()
    container = docker_client.containers.run(
        "test-image:latest",
        detach=True,
        remove=True,
    )

    try:
        DockerTestUtils.wait_for_container_health(container, timeout=TEST_TIMEOUTS["startup"])
        startup_time = time.time() - start_time

        assert startup_time <= PERFORMANCE_THRESHOLDS["startup_time"], (
            f"Container startup took {startup_time:.1f}s, exceeding threshold of "
            f"{PERFORMANCE_THRESHOLDS['startup_time']}s"
        )
    finally:
        container.stop()


def test_entrypoint_execution(running_container: Dict[str, Any]) -> None:
    """Test that container entrypoint executes correctly."""
    # Check process tree
    result = running_container.exec_run("ps -ef")
    assert result.exit_code == 0, "Failed to check process tree"

    processes = result.output.decode()
    assert "tini" in processes, "Init system (tini) not running"
    assert "python" in processes, "Main application process not running"


def test_graceful_shutdown(docker_client: Any) -> None:
    """Test that container shuts down gracefully."""
    container = docker_client.containers.run(
        "test-image:latest",
        detach=True,
        remove=True,
    )

    try:
        # Wait for container to be healthy
        DockerTestUtils.wait_for_container_health(container)

        # Send SIGTERM
        start_time = time.time()
        container.stop(timeout=10)
        shutdown_time = time.time() - start_time

        # Check logs for graceful shutdown messages
        logs = container.logs().decode()
        assert any(
            msg in logs.lower() for msg in ["shutdown", "stopping", "terminated"]
        ), "No graceful shutdown message found in logs"

        assert shutdown_time < 10, f"Container took too long to shutdown: {shutdown_time:.1f}s"
    except (docker.errors.APIError, docker.errors.ContainerError):
        container.remove(force=True)
        raise
