"""Test container health check functionality."""

import time
from typing import Any

import pytest

from ..config.test_config import TEST_TIMEOUTS
from ..utils.docker_test_utils import DockerTestUtils


def test_health_check_configuration(docker_client: Any) -> None:
    """Test that health check is properly configured."""
    image = docker_client.images.get("test-image:latest")
    config = image.attrs["Config"]

    assert "Healthcheck" in config, "No health check configured in image"
    healthcheck = config["Healthcheck"]

    # Verify health check command
    assert healthcheck["Test"], "No health check command specified"
    assert healthcheck["Interval"], "No health check interval specified"
    assert healthcheck["Timeout"], "No health check timeout specified"
    assert healthcheck["Retries"], "No health check retries specified"


@pytest.mark.timeout(TEST_TIMEOUTS["health_check"])
def test_initial_health_check(docker_client: Any) -> None:
    """Test that container becomes healthy after startup."""
    container = docker_client.containers.run(
        "test-image:latest",
        detach=True,
        remove=True,
    )

    try:
        # Wait for container to become healthy
        assert DockerTestUtils.wait_for_container_health(
            container, timeout=TEST_TIMEOUTS["health_check"]
        ), "Container failed to become healthy"
    finally:
        container.stop()


def test_health_check_failure_handling(docker_client: Any) -> None:
    """Test container behavior when health checks fail."""
    # Start container with modified health check command that will fail
    container = docker_client.containers.run(
        "test-image:latest",
        detach=True,
        remove=True,
        healthcheck={
            "test": ["CMD-SHELL", "exit 1"],
            "interval": 1000000000,  # 1s in nanoseconds
            "timeout": 1000000000,
            "retries": 3,
        },
    )

    try:
        time.sleep(5)  # Wait for health checks to run
        container.reload()

        health_status = container.attrs["State"]["Health"]["Status"]
        assert health_status == "unhealthy", "Container should be marked as unhealthy"

        # Verify health check logs
        health_log = container.attrs["State"]["Health"]["Log"]
        assert len(health_log) > 0, "No health check logs found"
        assert any(
            entry["ExitCode"] != 0 for entry in health_log
        ), "No failed health checks recorded"
    finally:
        container.stop()


def test_health_check_recovery(docker_client: Any) -> None:
    """Test that container can recover from failed health checks."""
    container = docker_client.containers.run(
        "test-image:latest",
        detach=True,
        remove=True,
        environment={"SIMULATE_FAILURE": "true"},
    )

    try:
        # Wait for initial health check failure
        time.sleep(5)
        container.reload()

        # Trigger recovery
        container.exec_run("rm /tmp/simulate_failure")

        # Wait for recovery
        assert DockerTestUtils.wait_for_container_health(
            container, timeout=TEST_TIMEOUTS["health_check"]
        ), "Container failed to recover health"

        # Verify recovery in logs
        logs = container.logs().decode()
        assert any(
            "health check recovered" in line.lower() for line in logs.split("\n")
        ), "No health recovery message in logs"
    finally:
        container.stop()
