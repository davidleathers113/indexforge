"""Test container resource usage and limits."""

from typing import Any

import docker

from ..config.test_config import PERFORMANCE_THRESHOLDS, RESOURCE_LIMITS
from ..utils.docker_test_utils import DockerTestUtils


def test_memory_limits(docker_client: Any) -> None:
    """Test that container respects memory limits."""
    container = docker_client.containers.run(
        "test-image:latest",
        detach=True,
        remove=True,
        mem_limit=RESOURCE_LIMITS["memory"],
        memswap_limit=RESOURCE_LIMITS["memory"],  # Disable swap
    )

    try:
        # Wait for container to be ready
        DockerTestUtils.wait_for_container_health(container)

        # Monitor memory usage
        stats = DockerTestUtils.get_container_resource_usage(container)
        assert stats["memory_usage"] <= PERFORMANCE_THRESHOLDS["memory_usage"], (
            f"Memory usage {stats['memory_usage']:.1f}% exceeds threshold of "
            f"{PERFORMANCE_THRESHOLDS['memory_usage']}%"
        )
    finally:
        container.stop()


def test_cpu_limits(docker_client: Any) -> None:
    """Test that container respects CPU limits."""
    container = docker_client.containers.run(
        "test-image:latest",
        detach=True,
        remove=True,
        cpu_quota=int(RESOURCE_LIMITS["cpu_count"] * 100000),
        cpu_period=100000,
    )

    try:
        # Wait for container to be ready
        DockerTestUtils.wait_for_container_health(container)

        # Monitor CPU usage
        stats = DockerTestUtils.get_container_resource_usage(container)
        assert stats["cpu_usage"] <= PERFORMANCE_THRESHOLDS["cpu_usage"], (
            f"CPU usage {stats['cpu_usage']:.1f}% exceeds threshold of "
            f"{PERFORMANCE_THRESHOLDS['cpu_usage']}%"
        )
    finally:
        container.stop()


def test_pids_limit(docker_client: Any) -> None:
    """Test that container respects process limits."""
    container = docker_client.containers.run(
        "test-image:latest",
        detach=True,
        remove=True,
        pids_limit=RESOURCE_LIMITS["pids_limit"],
    )

    try:
        # Wait for container to be ready
        DockerTestUtils.wait_for_container_health(container)

        # Check current process count
        result = container.exec_run("ps aux | wc -l")
        assert result.exit_code == 0, "Failed to count processes"

        process_count = int(result.output.decode().strip())
        assert process_count <= PERFORMANCE_THRESHOLDS["max_processes"], (
            f"Process count {process_count} exceeds threshold of "
            f"{PERFORMANCE_THRESHOLDS['max_processes']}"
        )
    finally:
        container.stop()


def test_file_descriptors_limit(docker_client: Any) -> None:
    """Test that container respects file descriptor limits."""
    container = docker_client.containers.run(
        "test-image:latest",
        detach=True,
        remove=True,
        ulimits=[
            docker.types.Ulimit(
                name="nofile",
                soft=RESOURCE_LIMITS["ulimits"]["nofile"]["soft"],
                hard=RESOURCE_LIMITS["ulimits"]["nofile"]["hard"],
            )
        ],
    )

    try:
        # Wait for container to be ready
        DockerTestUtils.wait_for_container_health(container)

        # Check current file descriptor limits
        result = container.exec_run("ulimit -n")
        assert result.exit_code == 0, "Failed to check file descriptor limits"

        fd_limit = int(result.output.decode().strip())
        assert fd_limit <= RESOURCE_LIMITS["ulimits"]["nofile"]["soft"], (
            f"File descriptor limit {fd_limit} exceeds configured soft limit of "
            f"{RESOURCE_LIMITS['ulimits']['nofile']['soft']}"
        )
    finally:
        container.stop()
