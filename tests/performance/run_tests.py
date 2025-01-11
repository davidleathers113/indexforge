"""Script to run performance tests for both Weaviate versions."""

import os
import subprocess
import time
from datetime import datetime

import docker
import weaviate
from loguru import logger

from tests.performance.weaviate_performance_test import WeaviatePerformanceTest


def wait_for_weaviate(url: str, timeout: int = 300):
    """Wait for Weaviate to be ready.

    Args:
        url: Weaviate URL
        timeout: Timeout in seconds
    """
    client = weaviate.Client(url)
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            if client.is_ready():
                logger.info("Weaviate is ready")
                return True
        except Exception as e:
            logger.debug(f"Waiting for Weaviate: {e}")
        time.sleep(5)

    raise TimeoutError("Weaviate failed to become ready")


def run_weaviate_version(version: str, port: int = 8080) -> str:
    """Run Weaviate container with specified version.

    Args:
        version: Weaviate version
        port: Port to expose

    Returns:
        Container ID
    """
    client = docker.from_env()

    # Pull image
    image = f"semitechnologies/weaviate:{version}"
    logger.info(f"Pulling Weaviate image: {image}")
    client.images.pull(image)

    # Run container
    container = client.containers.run(
        image=image,
        environment={
            "QUERY_DEFAULTS_LIMIT": "25",
            "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED": "true",
            "DEFAULT_VECTORIZER_MODULE": "text2vec-transformers",
            "ENABLE_MODULES": "text2vec-transformers",
            "TRANSFORMERS_INFERENCE_API": "http://t2v-transformers:8080",
        },
        ports={f"{port}/tcp": port},
        detach=True,
    )

    # Wait for container to be ready
    logger.info("Waiting for Weaviate to be ready")
    wait_for_weaviate(f"http://localhost:{port}")

    return container.id


def stop_container(container_id: str):
    """Stop and remove container.

    Args:
        container_id: Container ID
    """
    client = docker.from_env()
    container = client.containers.get(container_id)

    logger.info(f"Stopping container: {container_id}")
    container.stop()

    logger.info(f"Removing container: {container_id}")
    container.remove()


def run_version_tests(version: str, port: int = 8080):
    """Run performance tests for specific version.

    Args:
        version: Weaviate version
        port: Port to expose
    """
    try:
        # Start Weaviate
        container_id = run_weaviate_version(version, port)

        try:
            # Initialize client and run tests
            client = weaviate.Client(f"http://localhost:{port}")
            test = WeaviatePerformanceTest(client)

            # Run performance test
            test.run_performance_test()

            # Save results
            test.save_results(
                f"tests/performance/results_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

        finally:
            # Clean up container
            stop_container(container_id)

    except Exception as e:
        logger.error(f"Error running tests for version {version}: {e}")
        raise


def main():
    """Run performance tests for both versions."""
    # Ensure output directory exists
    os.makedirs("tests/performance", exist_ok=True)

    # Run tests for v3
    logger.info("Running tests for Weaviate v3.24.1")
    run_version_tests("3.24.1", port=8080)

    # Run tests for v4
    logger.info("Running tests for Weaviate v4.10.2")
    run_version_tests("4.10.2", port=8080)

    # Generate comparison report
    logger.info("Generating comparison report")
    subprocess.run(["python", "tests/performance/run_comparison.py"], check=True)


if __name__ == "__main__":
    main()
