"""Shared fixtures and utilities for log validation tests."""

import json
import logging
from typing import Any, Dict, List, Optional, Set

import pytest

from src.configuration.logger_setup import setup_json_logger


def create_test_log_entry(
    message: str,
    thread_id: int,
    sequence: Optional[int] = None,
    **extras: Any,
) -> Dict[str, Any]:
    """Create a standardized log entry for testing.

    Args:
        message: The log message
        thread_id: The thread identifier
        sequence: The sequence number
        **extras: Additional fields to include

    Returns:
        A dictionary containing the log entry
    """
    entry = {
        "message": message,
        "thread_id": thread_id,
        **extras,
    }
    if sequence is not None:
        entry["sequence"] = sequence
    return entry


def verify_log_structure(
    entry: Dict[str, Any],
    required_fields: Set[str],
    optional_fields: Optional[Set[str]] = None,
) -> None:
    """Verify basic log entry structure.

    Args:
        entry: The log entry to verify
        required_fields: Set of fields that must be present
        optional_fields: Set of fields that may be present

    Raises:
        AssertionError: If the entry structure is invalid
    """
    # Check required fields
    for field in required_fields:
        assert field in entry, f"Missing required field: {field}"

    # Check no unexpected fields
    if optional_fields is not None:
        allowed_fields = required_fields | optional_fields
        unexpected = set(entry.keys()) - allowed_fields
        assert not unexpected, f"Unexpected fields found: {unexpected}"


@pytest.fixture
def json_logger(temp_log_file: str, cleanup_logger: Any) -> logging.Logger:
    """Create a JSON logger for testing.

    Args:
        temp_log_file: Path to temporary log file
        cleanup_logger: Fixture to clean up logger after test

    Returns:
        Configured JSON logger
    """
    return setup_json_logger("test_logger", temp_log_file)


@pytest.fixture
def write_test_logs(temp_log_file: str) -> None:
    """Write test log entries to a file.

    Args:
        temp_log_file: Path to temporary log file
    """

    def _write_logs(entries: List[Dict[str, Any]]) -> None:
        with open(temp_log_file, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

    return _write_logs

import tracemalloc

def pytest_configure(config):
    """Configure pytest with enhanced exception handling."""
    tracemalloc.start()

def pytest_unconfigure(config):
    """Cleanup pytest configuration."""
    tracemalloc.stop()
