import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, Generator, List

import aiohttp
import docker
import psutil
import pytest
from docker.models.containers import Container


@pytest.fixture(scope="function")
async def running_app(
    docker_client: docker.DockerClient, dockerfile: Path, test_environment: Dict[str, str]
) -> Generator[Container, None, None]:
    """Provide a running application container for performance testing."""
    # Build image
    image, _ = docker_client.images.build(
        path=str(dockerfile.parent),
        dockerfile=str(dockerfile.name),
        rm=True,
        buildargs=test_environment,
    )

    # Run container with resource limits
    container = docker_client.containers.run(
        image.id,
        detach=True,
        environment=test_environment,
        ports={"8000/tcp": None},
        mem_limit="1g",
        cpus=1.0,
        healthcheck={
            "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
            "interval": 10000000000,
            "timeout": 5000000000,
            "retries": 3,
        },
    )

    # Wait for container to be healthy
    start_time = time.time()
    while time.time() - start_time < 30:
        container.reload()
        health = container.attrs["State"].get("Health", {}).get("Status")
        if health == "healthy":
            break
        await asyncio.sleep(1)
    else:
        pytest.fail("Container failed to become healthy")

    yield container

    container.stop(timeout=1)
    container.remove(force=True)


async def make_request(session: aiohttp.ClientSession, url: str) -> float:
    """Make a single HTTP request and return response time."""
    start_time = time.time()
    async with session.get(url) as response:
        await response.text()
        return time.time() - start_time


@pytest.mark.asyncio
async def test_load_performance(running_app: Container) -> None:
    """Test application performance under load."""
    port = running_app.attrs["NetworkSettings"]["Ports"]["8000/tcp"][0]["HostPort"]
    url = f"http://localhost:{port}/health"

    # Test parameters
    NUM_REQUESTS = 100
    MAX_CONCURRENT = 10
    MAX_AVG_RESPONSE_TIME = 0.5  # seconds

    async with aiohttp.ClientSession() as session:
        # Create tasks for concurrent requests
        tasks = []
        for _ in range(NUM_REQUESTS):
            tasks.append(make_request(session, url))

        # Execute requests with concurrency limit
        response_times = []
        for i in range(0, len(tasks), MAX_CONCURRENT):
            batch = tasks[i : i + MAX_CONCURRENT]
            batch_results = await asyncio.gather(*batch)
            response_times.extend(batch_results)

        # Calculate metrics
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]

        # Assert performance criteria
        assert (
            avg_response_time <= MAX_AVG_RESPONSE_TIME
        ), f"Average response time {avg_response_time:.3f}s exceeds {MAX_AVG_RESPONSE_TIME}s"
        assert (
            max_response_time <= MAX_AVG_RESPONSE_TIME * 3
        ), f"Maximum response time {max_response_time:.3f}s is too high"
        assert (
            p95_response_time <= MAX_AVG_RESPONSE_TIME * 2
        ), f"95th percentile response time {p95_response_time:.3f}s is too high"


def test_memory_leak(running_app: Container) -> None:
    """Test for memory leaks during extended operation."""
    DURATION = 60  # seconds
    POLL_INTERVAL = 5  # seconds
    MAX_MEMORY_GROWTH = 50  # MB

    # Initial memory usage
    stats = running_app.stats(stream=False)
    initial_memory = stats["memory_stats"]["usage"] / (1024 * 1024)  # Convert to MB

    memory_readings = [initial_memory]
    end_time = time.time() + DURATION

    # Monitor memory usage over time
    while time.time() < end_time:
        time.sleep(POLL_INTERVAL)
        stats = running_app.stats(stream=False)
        memory_usage = stats["memory_stats"]["usage"] / (1024 * 1024)
        memory_readings.append(memory_usage)

    # Calculate memory growth
    memory_growth = max(memory_readings) - min(memory_readings)
    assert (
        memory_growth <= MAX_MEMORY_GROWTH
    ), f"Memory growth of {memory_growth:.2f}MB exceeds limit of {MAX_MEMORY_GROWTH}MB"


def test_cpu_utilization(running_app: Container) -> None:
    """Test CPU utilization under normal operation."""
    DURATION = 30  # seconds
    MAX_CPU_PERCENT = 80

    # Monitor CPU usage
    cpu_readings = []
    end_time = time.time() + DURATION

    while time.time() < end_time:
        stats = running_app.stats(stream=False)
        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        system_delta = (
            stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
        )

        if system_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * 100
            cpu_readings.append(cpu_percent)

        time.sleep(1)

    avg_cpu = sum(cpu_readings) / len(cpu_readings)
    assert (
        avg_cpu <= MAX_CPU_PERCENT
    ), f"Average CPU utilization {avg_cpu:.2f}% exceeds limit of {MAX_CPU_PERCENT}%"


@pytest.mark.asyncio
async def test_concurrent_connections(running_app: Container) -> None:
    """Test handling of concurrent connections."""
    port = running_app.attrs["NetworkSettings"]["Ports"]["8000/tcp"][0]["HostPort"]
    url = f"http://localhost:{port}/health"

    MAX_CONNECTIONS = 50
    REQUESTS_PER_CONNECTION = 10
    MAX_ERROR_RATE = 0.01

    async with aiohttp.ClientSession() as session:
        # Create multiple connections
        tasks = []
        for _ in range(MAX_CONNECTIONS):
            connection_tasks = [make_request(session, url) for _ in range(REQUESTS_PER_CONNECTION)]
            tasks.extend(connection_tasks)

        # Execute all requests
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Calculate error rate
        errors = sum(1 for r in results if isinstance(r, Exception))
        error_rate = errors / len(results)

        assert (
            error_rate <= MAX_ERROR_RATE
        ), f"Error rate {error_rate:.2%} exceeds maximum allowed {MAX_ERROR_RATE:.2%}"


def test_resource_limits_compliance(running_app: Container) -> None:
    """Test that container respects resource limits under load."""
    # Generate some load
    running_app.exec_run(
        "python3 -c 'import math; [math.factorial(1000) for _ in range(1000)]'", detach=True
    )

    time.sleep(5)  # Wait for load to register

    # Check resource usage
    stats = running_app.stats(stream=False)

    # Memory usage should be within limits
    memory_usage_mb = stats["memory_stats"]["usage"] / (1024 * 1024)
    memory_limit_mb = stats["memory_stats"]["limit"] / (1024 * 1024)
    assert (
        memory_usage_mb <= memory_limit_mb
    ), f"Memory usage {memory_usage_mb:.2f}MB exceeds limit {memory_limit_mb:.2f}MB"

    # CPU usage should be within limits
    cpu_percent = (
        stats["cpu_stats"]["cpu_usage"]["total_usage"] / stats["cpu_stats"]["system_cpu_usage"]
    ) * 100
    assert cpu_percent <= 100, f"CPU usage {cpu_percent:.2f}% exceeds 100% limit"
