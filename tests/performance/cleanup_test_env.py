"""Script to clean up test environment for Weaviate performance testing."""

import os

import docker
from loguru import logger


def load_environment() -> tuple[str, str]:
    """Load environment IDs from file.

    Returns:
        Tuple of (network_id, transformers_id)
    """
    env_file = "tests/performance/environment.txt"
    if not os.path.exists(env_file):
        logger.error(f"Environment file not found: {env_file}")
        raise FileNotFoundError(f"Environment file not found: {env_file}")

    env_vars = {}
    with open(env_file) as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                env_vars[key] = value

    network_id = env_vars.get("NETWORK_ID")
    transformers_id = env_vars.get("TRANSFORMERS_ID")

    if not network_id or not transformers_id:
        logger.error("Missing required environment IDs")
        raise ValueError("Missing required environment IDs")

    return network_id, transformers_id


def cleanup_container(client: docker.DockerClient, container_id: str):
    """Clean up a Docker container.

    Args:
        client: Docker client
        container_id: Container ID to remove
    """
    try:
        container = client.containers.get(container_id)
        logger.info(f"Stopping container: {container_id}")
        container.stop()
        logger.info(f"Removing container: {container_id}")
        container.remove()
    except docker.errors.NotFound:
        logger.warning(f"Container not found: {container_id}")
    except Exception as e:
        logger.error(f"Error cleaning up container {container_id}: {e}")


def cleanup_network(client: docker.DockerClient, network_id: str):
    """Clean up a Docker network.

    Args:
        client: Docker client
        network_id: Network ID to remove
    """
    try:
        network = client.networks.get(network_id)
        logger.info(f"Removing network: {network.name}")
        network.remove()
    except docker.errors.NotFound:
        logger.warning(f"Network not found: {network_id}")
    except Exception as e:
        logger.error(f"Error cleaning up network {network_id}: {e}")


def cleanup_environment():
    """Clean up the test environment."""
    try:
        # Load environment IDs
        network_id, transformers_id = load_environment()

        # Initialize Docker client
        client = docker.from_env()

        # Clean up containers
        cleanup_container(client, transformers_id)

        # Clean up network
        cleanup_network(client, network_id)

        # Remove environment file
        try:
            os.remove("tests/performance/environment.txt")
            logger.info("Removed environment file")
        except FileNotFoundError:
            pass

        logger.info("Test environment cleanup complete")

    except Exception as e:
        logger.error(f"Error cleaning up test environment: {e}")
        raise


def main():
    """Run cleanup."""
    cleanup_environment()


if __name__ == "__main__":
    main()
