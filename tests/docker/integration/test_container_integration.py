import time
from pathlib import Path
from typing import Dict, Generator, List

import docker
import pytest
import requests
from docker.models.containers import Container
from docker.models.networks import Network


@pytest.fixture(scope="function")
def docker_network(docker_client: docker.DockerClient) -> Generator[Network, None, None]:
    """Create a dedicated test network."""
    network = docker_client.networks.create("test_network", driver="bridge", check_duplicate=True)
    yield network
    network.remove()


@pytest.fixture(scope="function")
def service_containers(
    docker_client: docker.DockerClient,
    dockerfile: Path,
    docker_compose_file: Path,
    test_environment: Dict[str, str],
    docker_network: Network,
) -> Generator[List[Container], None, None]:
    """Start all required service containers."""
    containers = []
    try:
        # Build and start Redis
        redis = docker_client.containers.run(
            "redis:7-alpine",
            detach=True,
            name="test_redis",
            network=docker_network.name,
            healthcheck={
                "test": ["CMD", "redis-cli", "ping"],
                "interval": 1000000000,
                "timeout": 3000000000,
                "retries": 3,
            },
        )
        containers.append(redis)

        # Build and start main application
        image, _ = docker_client.images.build(
            path=str(dockerfile.parent),
            dockerfile=str(dockerfile.name),
            rm=True,
            buildargs=test_environment,
        )

        app = docker_client.containers.run(
            image.id,
            detach=True,
            name="test_app",
            network=docker_network.name,
            environment={**test_environment, "REDIS_HOST": "test_redis", "REDIS_PORT": "6379"},
            ports={"8000/tcp": None},
        )
        containers.append(app)

        # Wait for containers to be healthy
        for container in containers:
            wait_for_container_healthy(container)

        yield containers

    finally:
        for container in containers:
            container.stop(timeout=1)
            container.remove(force=True)


def wait_for_container_healthy(container: Container, timeout: int = 30) -> None:
    """Wait for container to become healthy."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        container.reload()
        health = container.attrs["State"].get("Health", {}).get("Status")
        if health == "healthy":
            return
        time.sleep(1)
    pytest.fail(f"Container {container.name} failed to become healthy within {timeout} seconds")


def test_network_connectivity(service_containers: List[Container], docker_network: Network) -> None:
    """Test network connectivity between containers."""
    app_container = next(c for c in service_containers if c.name == "test_app")

    # Test Redis connectivity from app container
    result = app_container.exec_run("nc -zv test_redis 6379")
    assert result.exit_code == 0, "App container cannot connect to Redis"

    # Verify network isolation
    networks = app_container.attrs["NetworkSettings"]["Networks"]
    assert len(networks) == 1, "Container should only be connected to test network"
    assert docker_network.name in networks, "Container not connected to test network"


def test_volume_persistence(docker_client: docker.DockerClient, docker_network: Network) -> None:
    """Test data persistence across container restarts."""
    volume = docker_client.volumes.create("test_data")
    try:
        # Start Redis with volume
        redis = docker_client.containers.run(
            "redis:7-alpine",
            detach=True,
            name="test_redis_persistence",
            network=docker_network.name,
            volumes={"test_data": {"bind": "/data", "mode": "rw"}},
            command="redis-server --appendonly yes",
        )

        # Write test data
        redis.exec_run("redis-cli set test_key test_value")

        # Restart container
        redis.restart()
        time.sleep(2)  # Wait for Redis to start

        # Verify data persists
        result = redis.exec_run("redis-cli get test_key")
        assert (
            result.output.decode().strip() == "test_value"
        ), "Data did not persist across container restart"

    finally:
        redis.stop(timeout=1)
        redis.remove(force=True)
        volume.remove(force=True)


def test_environment_variables(service_containers: List[Container]) -> None:
    """Test environment variable handling."""
    app_container = next(c for c in service_containers if c.name == "test_app")

    # Check environment variables are set
    env_vars = app_container.attrs["Config"]["Env"]
    required_vars = {"REDIS_HOST", "REDIS_PORT", "ENVIRONMENT"}

    for var in required_vars:
        assert any(
            v.startswith(f"{var}=") for v in env_vars
        ), f"Required environment variable {var} not set"


def test_container_communication(service_containers: List[Container]) -> None:
    """Test inter-container communication via API calls."""
    app_container = next(c for c in service_containers if c.name == "test_app")

    # Get the exposed port
    port = app_container.attrs["NetworkSettings"]["Ports"]["8000/tcp"][0]["HostPort"]

    # Test API endpoint
    response = requests.get(f"http://localhost:{port}/health")
    assert response.status_code == 200, "Health check endpoint failed"

    # Test Redis integration via API
    response = requests.post(
        f"http://localhost:{port}/api/v1/test", json={"key": "test", "value": "data"}
    )
    assert response.status_code in {200, 201}, "Failed to store data in Redis"
