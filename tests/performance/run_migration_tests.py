"""Main script to run Weaviate migration performance tests."""

import argparse
import os
import subprocess
import sys

from loguru import logger


def run_command(command: str, description: str) -> bool:
    """Run a command and handle errors.

    Args:
        command: Command to run
        description: Description of the command

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Starting: {description}")
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"Completed: {description}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Error during {description}:")
        logger.error(f"Exit code: {e.returncode}")
        logger.error(f"Output: {e.output}")
        logger.error(f"Error: {e.stderr}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error during {description}: {e}")
        return False


def setup_environment() -> bool:
    """Set up test environment.

    Returns:
        True if successful, False otherwise
    """
    return run_command("python tests/performance/setup_test_env.py", "Setting up test environment")


def run_performance_tests() -> bool:
    """Run performance tests.

    Returns:
        True if successful, False otherwise
    """
    return run_command("python tests/performance/run_tests.py", "Running performance tests")


def cleanup_environment() -> bool:
    """Clean up test environment.

    Returns:
        True if successful, False otherwise
    """
    return run_command(
        "python tests/performance/cleanup_test_env.py", "Cleaning up test environment"
    )


def setup_logging(verbose: bool):
    """Set up logging configuration.

    Args:
        verbose: Whether to enable debug logging
    """
    # Remove default handler
    logger.remove()

    # Add custom handler
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    # Add console handler
    level = "DEBUG" if verbose else "INFO"
    logger.add(sys.stderr, format=log_format, level=level)

    # Add file handler
    os.makedirs("tests/performance/logs", exist_ok=True)
    logger.add(
        "tests/performance/logs/migration_test_{time}.log",
        format=log_format,
        level="DEBUG",
        rotation="1 day",
        retention="1 week",
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run Weaviate migration performance tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--skip-cleanup", action="store_true", help="Skip environment cleanup")
    return parser.parse_args()


def main():
    """Run migration performance tests."""
    # Parse arguments
    args = parse_args()

    # Set up logging
    setup_logging(args.verbose)

    try:
        logger.info("Starting migration performance tests")

        # Set up environment
        if not setup_environment():
            logger.error("Failed to set up test environment")
            sys.exit(1)

        try:
            # Run performance tests
            if not run_performance_tests():
                logger.error("Performance tests failed")
                sys.exit(1)

        finally:
            # Clean up environment
            if not args.skip_cleanup:
                if not cleanup_environment():
                    logger.error("Failed to clean up test environment")
                    sys.exit(1)
            else:
                logger.info("Skipping environment cleanup")

        logger.info("Migration performance tests completed successfully")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
