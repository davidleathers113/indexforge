"""Module for loading and managing test result data."""

import json
import os
from typing import Dict, Optional

from loguru import logger


def load_results(filepath: str) -> Dict:
    """Load test results from a JSON file.

    Args:
        filepath: Path to the JSON results file

    Returns:
        Dictionary containing test results

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        with open(filepath, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"Results file not found: {filepath}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in results file {filepath}: {e}")
        raise


def find_latest_results(directory: str, version_prefix: str) -> Optional[Dict]:
    """Find the latest test results for a specific version prefix.

    Args:
        directory: Directory containing result files
        version_prefix: Version prefix to search for (e.g., "3." or "4.")

    Returns:
        Latest results dictionary or None if no matching results found
    """
    latest_results = None
    latest_timestamp = None

    try:
        for filename in os.listdir(directory):
            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(directory, filename)
            try:
                results = load_results(filepath)
                version = results.get("weaviate_version", "")
                timestamp = results.get("timestamp")

                if not version.startswith(version_prefix) or not timestamp:
                    continue

                if latest_timestamp is None or timestamp > latest_timestamp:
                    latest_results = results
                    latest_timestamp = timestamp

            except (FileNotFoundError, json.JSONDecodeError):
                continue

        if latest_results is None:
            logger.warning(f"No results found for version {version_prefix}")

        return latest_results

    except Exception as e:
        logger.error(f"Error finding latest results: {e}")
        return None
