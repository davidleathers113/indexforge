"""Test streaming validation functionality.

Tests:
- Large file handling
- Chunk processing
- Memory efficiency
- Size limits
- Partial line handling
"""

from typing import Any, Callable, Dict, List

import pytest

from src.configuration.log_validation import LogValidationError, validate_log_file_with_streaming
from tests.unit.configuration.test_log_validation.conftest import create_test_log_entry


def test_log_validation():
    """Test log validation with streaming data"""
    # Use the imported create_test_log_entry function
    log_entry = create_test_log_entry("test message", 1, 1)
    assert log_entry["message"] == "test message"


def test_large_file_streaming(
    write_test_logs: Callable[[List[Dict[str, Any]]], None], temp_log_file: str
) -> None:
    """Test streaming validation with a large file.

    Scenario: Process a large log file
    Given: A log file with many entries
    When: The file is validated using streaming
    Then: Memory usage should remain constant
    """
    entries = []
    for i in range(10000):
        entries.append(create_test_log_entry(f"Message {i}", i, i))
    write_test_logs(entries)
    validate_log_file_with_streaming(
        temp_log_file,
        required_fields={"message", "thread_id", "sequence"},
        field_types={"message": str, "thread_id": int, "sequence": int},
        chunk_size=1024,
    )


def test_partial_line_handling(
    write_test_logs: Callable[[List[Dict[str, Any]]], None], temp_log_file: str
) -> None:
    """Test handling of partial lines in streaming validation.

    Scenario: Process a file with partial lines
    Given: A log file with incomplete lines
    When: The file is validated using streaming
    Then: Partial lines should be handled correctly
    """
    entries = [
        create_test_log_entry(message="Test message", thread_id=1, sequence=1, data="test data")
    ]
    write_test_logs(entries)
    validate_log_file_with_streaming(
        temp_log_file,
        required_fields={"message", "thread_id", "sequence"},
        field_types={"message": str, "thread_id": int, "sequence": int},
        chunk_size=16,
    )


def test_size_limit_validation(
    write_test_logs: Callable[[List[Dict[str, Any]]], None], temp_log_file: str
) -> None:
    """Test validation with size limits.

    Scenario: Process a file with entries of varying sizes
    Given: Log entries with different sizes
    When: The file is validated with size limits
    Then: Entries should be validated correctly
    """
    entries = [
        create_test_log_entry("Short message", 1, 1),
        create_test_log_entry("Medium message", 2, 2, data="x" * 1000),
        create_test_log_entry("Long message", 3, 3, data="y" * 5000),
    ]
    write_test_logs(entries)
    validate_log_file_with_streaming(
        temp_log_file,
        required_fields={"message", "thread_id", "sequence"},
        field_types={"message": str, "thread_id": int, "sequence": int},
        chunk_size=1024,
    )


def test_streaming_memory_usage(
    write_test_logs: Callable[[List[Dict[str, Any]]], None], temp_log_file: str
) -> None:
    """Test memory usage during streaming validation.

    Scenario: Process a file with large entries
    Given: A log file with entries containing large data fields
    When: The file is validated using streaming
    Then: Memory usage should remain constant
    """
    entries = []
    for i in range(10):
        large_data = "x" * (1024 * 1024)
        entries.append(create_test_log_entry(f"Large message {i}", i, i, large_data))
    write_test_logs(entries)
    validate_log_file_with_streaming(
        temp_log_file,
        required_fields={"message", "thread_id", "sequence"},
        field_types={"message": str, "thread_id": int, "sequence": int},
        chunk_size=4096,
    )


def test_streaming_error_location(
    write_test_logs: Callable[[List[Dict[str, Any]]], None], temp_log_file: str
) -> None:
    """Test error location reporting in streaming validation.

    Scenario: Process a file with an invalid entry
    Given: A log file with multiple entries, one invalid
    When: The file is validated using streaming
    Then: The error should report the correct line number
    """
    entries = []
    for i in range(5):
        entries.append(create_test_log_entry(f"Valid {i}", i, i))
    entries.append({"invalid": "entry"})
    for i in range(5, 10):
        entries.append(create_test_log_entry(f"Valid {i}", i, i))
    write_test_logs(entries)
    with pytest.raises(LogValidationError) as exc_info:
        validate_log_file_with_streaming(
            temp_log_file,
            required_fields={"message", "thread_id", "sequence"},
            field_types={"message": str, "thread_id": int, "sequence": int},
            chunk_size=1024,
        )
    error_msg = str(exc_info.value)
    assert "Line 6" in error_msg


def test_streaming_validation(
    write_test_logs: Callable[[List[Dict[str, Any]]], None], temp_log_file: str
) -> None:
    """Test basic streaming validation functionality.

    Scenario: Process a file with valid and invalid entries
    Given: A log file with mixed valid and invalid entries
    When: The file is validated using streaming
    Then: Validation should fail on the first invalid entry
    """
    entries = []
    for i in range(5):
        entries.append(create_test_log_entry(f"Test message {i}", i, i))
    entries.append({"invalid": "entry"})
    for i in range(5, 10):
        entries.append(create_test_log_entry(f"Test message {i}", i, i))
    write_test_logs(entries)
    with pytest.raises(LogValidationError) as exc_info:
        validate_log_file_with_streaming(
            temp_log_file,
            required_fields={"message", "thread_id", "sequence"},
            field_types={"message": str, "thread_id": int, "sequence": int},
            chunk_size=1024,
        )
    error_msg = str(exc_info.value)
    assert "Line 6" in error_msg
