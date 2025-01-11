"""Streaming log validation tests."""

import json
import logging
import time
from typing import Any, Dict, List

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.configuration.logger_setup import log_with_context, setup_json_logger
from tests.unit.configuration.test_logger_validation import (
    LogValidationError,
    validate_log_file,
    validate_log_file_with_streaming,
)


def test_streaming_validation_large_file(temp_log_file: str, cleanup_logger: Any) -> None:
    """Test streaming validation with a large log file.

    This test verifies that large files can be processed efficiently using
    the streaming validator.

    Args:
        temp_log_file: Path to temporary log file
        cleanup_logger: Fixture to clean up logger after test
    """
    logger = setup_json_logger("test_logger", temp_log_file)
    for i in range(1000):
        log_with_context(
            logger, logging.INFO, "Message %d" % i, {"thread_id": i, "timestamp": time.time()}
        )
    validate_log_file_with_streaming(
        temp_log_file,
        required_fields={"message", "thread_id"},
        field_types={"message": str, "thread_id": int},
        chunk_size=1024,
    )


def test_streaming_validation_with_size_limits(temp_log_file: str, cleanup_logger: Any) -> None:
    """Test streaming validation with field size limits.

    Args:
        temp_log_file: Path to temporary log file
        cleanup_logger: Fixture to clean up logger after test
    """
    with open(temp_log_file, "w", encoding="utf-8") as f:
        f.write(json.dumps({"message": "Short message", "thread_id": 123}) + "\n")
        f.write(json.dumps({"message": "x" * 1000, "thread_id": 456}) + "\n")
    with pytest.raises(LogValidationError) as exc_info:
        validate_log_file_with_streaming(
            temp_log_file,
            required_fields={"message", "thread_id"},
            field_types={"message": str, "thread_id": int},
            max_sizes={"message": 100},
        )
    assert "exceeds maximum size" in str(exc_info.value)


@given(
    st.lists(
        st.fixed_dictionaries(
            {
                "message": st.text(min_size=1),
                "thread_id": st.integers(),
                "extra": st.one_of(st.text(), st.integers(), st.floats(allow_nan=False)),
            }
        ),
        min_size=1,
    )
)
@settings(max_examples=100)
def test_streaming_with_data(
    temp_log_file: str, cleanup_logger: Any, entries: List[Dict[str, Any]]
) -> None:
    """Property-based test for streaming validation.

    Args:
        temp_log_file: Path to temporary log file
        cleanup_logger: Fixture to clean up logger after test
        entries: Generated test data
    """
    with open(temp_log_file, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    try:
        with open(temp_log_file, "r", encoding="utf-8") as f:
            standard_result = validate_log_file(
                f.readlines(),
                required_fields={"message", "thread_id"},
                field_types={"message": str, "thread_id": int},
            )
        streaming_result = validate_log_file_with_streaming(
            temp_log_file,
            required_fields={"message", "thread_id"},
            field_types={"message": str, "thread_id": int},
        )
        assert len(standard_result) == len(streaming_result)
        for std_entry, stream_entry in zip(standard_result, streaming_result):
            assert std_entry == stream_entry
    except Exception as e:
        pytest.fail(f"Validation failed: {str(e)}")
