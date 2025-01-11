"""Basic logger functionality tests."""

import logging
import threading
from typing import Any

import pytest

from src.configuration.logger_setup import log_with_context, setup_json_logger
from tests.unit.configuration.test_logger_validation import (
    LogFieldError,
    LogFormatError,
    validate_log_file,
)


def test_concurrent_logging(temp_log_file: str, cleanup_logger: Any) -> None:
    """Test logging from multiple threads.

    Args:
        temp_log_file: Path to temporary log file
        cleanup_logger: Fixture to clean up logger after test

    Raises:
        PermissionError: If log file cannot be accessed
        IOError: If other file operations fail
        LogFormatError: If log entries are not valid JSON
        LogFieldError: If required fields are missing
        LogTypeError: If fields have incorrect types
    """
    logger = setup_json_logger("test_logger", temp_log_file)

    def log_messages() -> None:
        for i in range(10):
            log_with_context(
                logger, logging.INFO, "Message %d", {"thread_id": threading.get_ident()}
            )

    threads = [threading.Thread(target=log_messages) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    try:
        with open(temp_log_file, "r", encoding="utf-8") as f:
            log_lines = f.readlines()
            expected_count = 30
            if len(log_lines) != expected_count:
                raise ValueError(
                    "Unexpected number of log lines: got %d, expected %d"
                    % (len(log_lines), expected_count)
                )
            validated_entries = validate_log_file(
                log_lines,
                required_fields={"message", "thread_id"},
                field_types={"message": str, "thread_id": int},
            )
            thread_ids = {entry["thread_id"] for entry in validated_entries}
            assert len(thread_ids) == 3, "Expected logs from exactly 3 threads"
    except PermissionError as e:
        raise PermissionError("Permission denied accessing log file: %s" % str(e)) from e
    except (IOError, OSError) as e:
        raise IOError("Failed to read log file: %s" % str(e)) from e


def test_large_messages(temp_log_file: str, cleanup_logger: Any) -> None:
    """Test handling of large log messages with Unicode characters.

    Args:
        temp_log_file: Path to temporary log file
        cleanup_logger: Fixture to clean up logger after test

    Raises:
        PermissionError: If log file cannot be accessed
        IOError: If other file operations fail
        LogFormatError: If log entries are not valid JSON
        LogFieldError: If required fields are missing
        LogTypeError: If fields have incorrect types
    """
    logger = setup_json_logger("test_logger", temp_log_file)
    large_message = "Large message " * 1000 + "🚀 💫 🌟"
    log_with_context(logger, logging.INFO, large_message, {"size": len(large_message)})
    try:
        with open(temp_log_file, "r", encoding="utf-8") as f:
            log_lines = f.readlines()
            validated_entries = validate_log_file(
                log_lines,
                required_fields={"message", "size"},
                field_types={"message": str, "size": int},
            )
            entry = validated_entries[0]
            assert entry["message"] == large_message
            assert entry["size"] == len(large_message)
    except PermissionError as e:
        raise PermissionError("Permission denied accessing log file: %s" % str(e)) from e
    except (IOError, OSError) as e:
        raise IOError("Failed to read log file: %s" % str(e)) from e


def test_malformed_json(temp_log_file: str, cleanup_logger: Any) -> None:
    """Test handling of malformed JSON in log files.

    Args:
        temp_log_file: Path to temporary log file
        cleanup_logger: Fixture to clean up logger after test
    """
    with open(temp_log_file, "w", encoding="utf-8") as f:
        f.write('{"message": "test", "thread_id": 123}\n')
        f.write('{"message": "incomplete"')
        f.write('{"message": 123, "thread_id": "invalid"}\n')
    with pytest.raises(LogFormatError) as exc_info:
        with open(temp_log_file, "r", encoding="utf-8") as f:
            validate_log_file(
                f.readlines(),
                required_fields={"message", "thread_id"},
                field_types={"message": str, "thread_id": int},
            )
    assert "Line 2: Invalid JSON" in str(exc_info.value)


def test_missing_fields(temp_log_file: str, cleanup_logger: Any) -> None:
    """Test handling of missing required fields.

    Args:
        temp_log_file: Path to temporary log file
        cleanup_logger: Fixture to clean up logger after test
    """
    with open(temp_log_file, "w", encoding="utf-8") as f:
        f.write('{"message": "test", "thread_id": 123}\n')
        f.write('{"message": "missing thread_id"}\n')
    with pytest.raises(LogFieldError) as exc_info:
        with open(temp_log_file, "r", encoding="utf-8") as f:
            validate_log_file(
                f.readlines(),
                required_fields={"message", "thread_id"},
                field_types={"message": str, "thread_id": int},
            )
    assert "Line 2: Missing required fields: thread_id" in str(exc_info.value)
