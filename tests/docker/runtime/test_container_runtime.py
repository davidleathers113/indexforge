import time
from pathlib import Path
from typing import Dict, Generator

import docker
import pytest
from docker.models.containers import Container


@pytest.fixture(scope="function")
def running_container(
    docker_client: docker.DockerClient, dockerfile: Path, test_environment: Dict[str, str]
) -> Generator[Container, None, None]:
    """Provide a running container for testing."""
    # Build image first
    image, _ = docker_client.images.build(
        path=str(dockerfile.parent),
        dockerfile=str(dockerfile.name),
        rm=True,
        buildargs=test_environment,
    )

    # Run container
    container = docker_client.containers.run(
        image.id,
        detach=True,
        environment=test_environment,
        ports={"8000/tcp": None},  # Dynamically assign port
        healthcheck={
            "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
            "interval": 10000000000,  # 10s in nanoseconds
            "timeout": 5000000000,  # 5s in nanoseconds
            "retries": 3,
            "start_period": 5000000000,  # 5s in nanoseconds
        },
    )

    yield container

    # Cleanup
    container.stop(timeout=1)
    container.remove(force=True)


def test_container_startup_time(
    docker_client: docker.DockerClient, dockerfile: Path, test_environment: Dict[str, str]
) -> None:
    """Test that container starts within acceptable time."""
    MAX_STARTUP_TIME = 10  # seconds

    start_time = time.time()
    container = None
    try:
        # Build image first
        image, _ = docker_client.images.build(
            path=str(dockerfile.parent),
            dockerfile=str(dockerfile.name),
            rm=True,
            buildargs=test_environment,
        )

        # Run container
        container = docker_client.containers.run(
            image.id, detach=True, environment=test_environment
        )

        # Wait for container to be running
        while container.status != "running":
            container.reload()
            if time.time() - start_time > MAX_STARTUP_TIME:
                pytest.fail(f"Container failed to start within {MAX_STARTUP_TIME} seconds")
            time.sleep(0.1)

        startup_time = time.time() - start_time
        assert (
            startup_time <= MAX_STARTUP_TIME
        ), f"Container startup took {startup_time:.2f}s, exceeding limit of {MAX_STARTUP_TIME}s"

    finally:
        if container:
            container.stop(timeout=1)
            container.remove(force=True)


def test_health_check(running_container: Container) -> None:
    """Test that container health check passes."""
    MAX_HEALTH_CHECK_TIME = 30  # seconds
    start_time = time.time()

    while running_container.attrs["State"].get("Health", {}).get("Status") != "healthy":
        if time.time() - start_time > MAX_HEALTH_CHECK_TIME:
            pytest.fail(
                f"Container failed to become healthy within {MAX_HEALTH_CHECK_TIME} seconds"
            )
        running_container.reload()
        time.sleep(1)

    health_status = running_container.attrs["State"]["Health"]["Status"]
    assert health_status == "healthy", f"Container health check failed. Status: {health_status}"


def test_resource_limits(running_container: Container) -> None:
    """Test that container respects resource limits."""
    # Get container stats
    stats = running_container.stats(stream=False)

    # CPU usage should be within limits
    cpu_percent = (
        stats["cpu_stats"]["cpu_usage"]["total_usage"]
        / stats["cpu_stats"]["system_cpu_usage"]
        * 100
    )
    assert cpu_percent <= 100, f"CPU usage {cpu_percent:.2f}% exceeds 100%"

    # Memory usage should be within limits
    memory_usage = stats["memory_stats"]["usage"] / (1024 * 1024)  # Convert to MB
    memory_limit = stats["memory_stats"]["limit"] / (1024 * 1024)
    assert (
        memory_usage <= memory_limit
    ), f"Memory usage {memory_usage:.2f}MB exceeds limit of {memory_limit:.2f}MB"


def test_non_root_user(running_container: Container) -> None:
    """Verify container runs as non-root user."""
    exec_result = running_container.exec_run("id -u")
    user_id = int(exec_result.output.decode().strip())
    assert user_id != 0, "Container should not run as root user"


def test_file_permissions(running_container: Container) -> None:
    """Test that file permissions are set correctly."""
    # Check app directory permissions
    exec_result = running_container.exec_run("ls -l /app")
    assert exec_result.exit_code == 0, "Failed to check app directory permissions"

    # Verify no world-writable files
    exec_result = running_container.exec_run("find /app -type f -perm -002")
    assert not exec_result.output.strip(), "Found world-writable files in /app"


def test_process_isolation(running_container: Container) -> None:
    """Test process isolation within container."""
    exec_result = running_container.exec_run("ps aux")
    processes = exec_result.output.decode().split("\n")

    # Should have minimal number of processes
    assert len(processes) < 10, "Too many processes running in container"

    # Main process should be our application
    assert any("python" in line for line in processes), "Main application process not found"
