"""
Utility functions for document lineage tracking.

This module provides reusable utility functions for:
- JSON file handling
- ISO date parsing and formatting
- Common operations used across modules
"""

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON data from a file.

    Args:
        path: Path to the JSON file

    Returns:
        Dictionary containing the loaded JSON data
    """
    try:
        with open(path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as error:
        logger.error(f"Error decoding JSON from {path}: {error}")
        return {}


def save_json(path: Path, data: Dict[str, Any], indent: int = 2) -> bool:
    """Save data to a JSON file.

    Args:
        path: Path to save the JSON file
        data: Data to save
        indent: Number of spaces for indentation

    Returns:
        True if save was successful, False otherwise
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=indent)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON data: {e}")
        return False


def parse_iso_datetime(date_str: str) -> Optional[datetime]:
    """Parse an ISO format datetime string.

    Args:
        date_str: ISO format datetime string

    Returns:
        Parsed datetime object or None if parsing fails
    """
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing datetime {date_str}: {e}")
        return None


def format_iso_datetime(dt: datetime) -> str:
    """Format a datetime object as ISO format string.

    Args:
        dt: Datetime object to format

    Returns:
        ISO format datetime string
    """
    return dt.isoformat()
