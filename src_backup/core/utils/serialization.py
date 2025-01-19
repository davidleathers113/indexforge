"""Serialization utilities for data handling.

This module provides reusable utility functions for:
- JSON file handling with atomic operations
- ISO date parsing and formatting
- Data serialization and deserialization
- Error handling and logging

Example:
    ```python
    from pathlib import Path
    from src.core.utils.serialization import JsonHandler

    # Initialize handler
    handler = JsonHandler()

    # Load data
    config = handler.load(Path("config.json"))

    # Save data atomically
    handler.save(Path("output.json"), data={"key": "value"})

    # Parse dates
    dt = handler.parse_iso_datetime("2024-01-17T12:00:00")
    ```
"""

from datetime import UTC, datetime
import json
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class SerializationError(Exception):
    """Base exception for serialization errors."""


class JsonLoadError(SerializationError):
    """Error loading JSON data."""


class JsonSaveError(SerializationError):
    """Error saving JSON data."""


class DateParseError(SerializationError):
    """Error parsing datetime string."""


class JsonHandler:
    """Handler for JSON file operations with atomic writes."""

    def __init__(self, encoding: str = "utf-8", indent: int = 2):
        """Initialize JSON handler.

        Args:
            encoding: File encoding to use.
            indent: Number of spaces for indentation.
        """
        self.encoding = encoding
        self.indent = indent

    def load(self, path: Path, default: dict | None = None) -> dict[str, Any]:
        """Load JSON data from a file.

        Args:
            path: Path to the JSON file.
            default: Default value if file doesn't exist or is invalid.

        Returns:
            Dictionary containing the loaded JSON data.

        Raises:
            JsonLoadError: If loading fails and no default provided.
        """
        try:
            with path.open(encoding=self.encoding) as f:
                return json.load(f)
        except FileNotFoundError:
            if default is not None:
                return default
            raise JsonLoadError(f"File not found: {path}")
        except json.JSONDecodeError as e:
            if default is not None:
                logger.warning(f"Invalid JSON in {path}, using default: {e}")
                return default
            raise JsonLoadError(f"Invalid JSON in {path}: {e}") from e
        except Exception as e:
            if default is not None:
                logger.error(f"Error loading {path}, using default: {e}")
                return default
            raise JsonLoadError(f"Error loading {path}: {e}") from e

    def save(
        self,
        path: Path,
        data: dict[str, Any],
        atomic: bool = True,
        create_parents: bool = True,
    ) -> None:
        """Save data to a JSON file atomically.

        Args:
            path: Path to save the JSON file.
            data: Data to save.
            atomic: Whether to use atomic write operations.
            create_parents: Whether to create parent directories.

        Raises:
            JsonSaveError: If saving fails.
        """
        if create_parents:
            path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if atomic:
                # Create temporary file in same directory
                tmp_path = path.with_suffix(".tmp")
                with tmp_path.open("w", encoding=self.encoding) as f:
                    json.dump(data, f, indent=self.indent, default=str)
                # Atomic rename
                tmp_path.replace(path)
            else:
                with path.open("w", encoding=self.encoding) as f:
                    json.dump(data, f, indent=self.indent, default=str)
        except Exception as e:
            raise JsonSaveError(f"Error saving to {path}: {e}") from e

    @staticmethod
    def parse_iso_datetime(date_str: str) -> datetime:
        """Parse an ISO format datetime string.

        Args:
            date_str: ISO format datetime string.

        Returns:
            Parsed datetime object.

        Raises:
            DateParseError: If parsing fails.
        """
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.replace(tzinfo=dt.tzinfo or UTC)
        except (ValueError, TypeError) as e:
            raise DateParseError(f"Invalid datetime format: {date_str}") from e

    @staticmethod
    def format_iso_datetime(dt: datetime) -> str:
        """Format a datetime object as ISO format string.

        Args:
            dt: Datetime object to format.

        Returns:
            ISO format datetime string.
        """
        return dt.isoformat()

    def merge_json_files(
        self,
        sources: list[Path],
        output: Path,
        skip_missing: bool = True,
    ) -> None:
        """Merge multiple JSON files into one.

        Args:
            sources: List of source file paths.
            output: Output file path.
            skip_missing: Whether to skip missing files.

        Raises:
            JsonLoadError: If loading fails and skip_missing is False.
            JsonSaveError: If saving fails.
        """
        merged = {}
        for path in sources:
            try:
                data = self.load(path)
                merged.update(data)
            except JsonLoadError:
                if not skip_missing:
                    raise
        self.save(output, merged)


json_handler = JsonHandler()  # Default instance for convenience
