"""Test container-to-container network communication."""

from typing import Any, Dict


from ...utils.docker_test_utils import DockerTestUtils


def test_dns_resolution(docker_client: Any, docker_network: Dict[str, Any]) -> None:
    """Test DNS resolution between containers."""
    # Start first container
    container1 = docker_client.containers.run(
        "test-image:latest",
        name="test-container1",
        network=docker_network["Name"],
        detach=True,
        remove=True,
    )

    # Start second container
    container2 = docker_client.containers.run(
        "test-image:latest",
        name="test-container2",
        network=docker_network["Name"],
        detach=True,
        remove=True,
    )

    try:
        # Wait for containers
        DockerTestUtils.wait_for_container_health(container1)
        DockerTestUtils.wait_for_container_health(container2)

        # Test DNS resolution from container1 to container2
        result = container1.exec_run("ping -c 1 test-container2")
        assert result.exit_code == 0, "Failed to resolve container2 from container1"

        # Test DNS resolution from container2 to container1
        result = container2.exec_run("ping -c 1 test-container1")
        assert result.exit_code == 0, "Failed to resolve container1 from container2"
    finally:
        container1.stop()
        container2.stop()


def test_service_communication(docker_client: Any, docker_network: Dict[str, Any]) -> None:
    """Test service-level communication between containers."""
    # Start Redis container
    redis = docker_client.containers.run(
        "redis:latest",
        name="test-redis",
        network=docker_network["Name"],
        detach=True,
        remove=True,
    )

    # Start app container
    app = docker_client.containers.run(
        "test-image:latest",
        name="test-app",
        network=docker_network["Name"],
        environment={"REDIS_HOST": "test-redis"},
        detach=True,
        remove=True,
    )

    try:
        # Wait for containers
        DockerTestUtils.wait_for_container_health(app)

        # Test Redis connection
        result = app.exec_run("redis-cli -h test-redis ping")
        assert result.exit_code == 0, "Failed to connect to Redis"
        assert b"PONG" in result.output, "Redis not responding correctly"
    finally:
        app.stop()
        redis.stop()
