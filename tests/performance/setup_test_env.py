"""Script to set up test environment for Weaviate performance testing."""

import time
from typing import List

import docker
from loguru import logger


def setup_transformers_module(port: int = 8081) -> str:
    """Set up text2vec-transformers module.

    Args:
        port: Port to expose

    Returns:
        Container ID
    """
    client = docker.from_env()

    # Pull image
    image = "semitechnologies/transformers-inference:sentence-transformers-all-MiniLM-L6-v2"
    logger.info(f"Pulling transformers image: {image}")
    client.images.pull(image)

    # Run container
    container = client.containers.run(
        image=image,
        environment={
            "ENABLE_CUDA": "0",
            "NVIDIA_VISIBLE_DEVICES": "",
        },
        ports={f"{port}/tcp": port},
        detach=True,
    )

    # Wait for container to be ready
    logger.info("Waiting for transformers module to be ready")
    time.sleep(30)  # Give it time to load the model

    return container.id


def setup_network() -> str:
    """Set up Docker network for test environment.

    Returns:
        Network ID
    """
    client = docker.from_env()

    # Create network if it doesn't exist
    network_name = "weaviate-test-network"
    try:
        network = client.networks.get(network_name)
        logger.info(f"Using existing network: {network_name}")
    except docker.errors.NotFound:
        network = client.networks.create(
            name=network_name,
            driver="bridge",
            check_duplicate=True,
        )
        logger.info(f"Created network: {network_name}")

    return network.id


def cleanup_environment(container_ids: List[str], network_id: str):
    """Clean up test environment.

    Args:
        container_ids: List of container IDs to remove
        network_id: Network ID to remove
    """
    client = docker.from_env()

    # Stop and remove containers
    for container_id in container_ids:
        try:
            container = client.containers.get(container_id)
            logger.info(f"Stopping container: {container_id}")
            container.stop()
            logger.info(f"Removing container: {container_id}")
            container.remove()
        except Exception as e:
            logger.error(f"Error cleaning up container {container_id}: {e}")

    # Remove network
    try:
        network = client.networks.get(network_id)
        logger.info(f"Removing network: {network.name}")
        network.remove()
    except Exception as e:
        logger.error(f"Error cleaning up network {network_id}: {e}")


def main():
    """Set up test environment."""
    try:
        # Create network
        network_id = setup_network()

        # Start transformers module
        transformers_id = setup_transformers_module()

        logger.info("Test environment setup complete")
        logger.info(f"Network ID: {network_id}")
        logger.info(f"Transformers container ID: {transformers_id}")

        # Write IDs to file for cleanup
        with open("tests/performance/environment.txt", "w") as f:
            f.write(f"NETWORK_ID={network_id}\n")
            f.write(f"TRANSFORMERS_ID={transformers_id}\n")

    except Exception as e:
        logger.error(f"Error setting up test environment: {e}")
        raise


if __name__ == "__main__":
    main()
