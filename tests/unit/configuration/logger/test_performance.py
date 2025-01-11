"""Logger performance benchmark tests."""

import logging
import time
from typing import Any

import pytest

from src.configuration.logger_setup import log_with_context, setup_json_logger
from tests.unit.configuration.test_logger_validation import (
    validate_log_file,
    validate_log_file_with_streaming,
)


@pytest.mark.benchmark
def test_validation_performance(temp_log_file: str, cleanup_logger: Any) -> None:
    """Benchmark validation performance with different file sizes.

    Args:
        temp_log_file: Path to temporary log file
        cleanup_logger: Fixture to clean up logger after test
    """
    logger = setup_json_logger("test_logger", temp_log_file)
    entry_counts = [10, 100, 1000]
    timings = {}

    for count in entry_counts:
        # Generate test data
        for i in range(count):
            log_with_context(
                logger, logging.INFO, "Message %d" % i, {"thread_id": i, "timestamp": time.time()}
            )

        # Test standard validation
        start_time = time.time()
        standard_result = []
        with open(temp_log_file, "r", encoding="utf-8") as f:
            standard_result = validate_log_file(
                f.readlines(),
                required_fields={"message", "thread_id"},
                field_types={"message": str, "thread_id": int},
            )
        standard_time = time.time() - start_time

        # Test streaming validation
        start_time = time.time()
        streaming_result = validate_log_file_with_streaming(
            temp_log_file,
            required_fields={"message", "thread_id"},
            field_types={"message": str, "thread_id": int},
        )
        streaming_time = time.time() - start_time

        # Record timings
        timings[count] = {"standard": standard_time, "streaming": streaming_time}

        # Verify results match
        assert len(standard_result) == len(streaming_result)
        for std_entry, stream_entry in zip(standard_result, streaming_result):
            assert std_entry == stream_entry

    # Report results
    for count, times in timings.items():
        print(
            f'Entries: {count}, Standard: {times["standard"]:.4f}s, '
            f'Streaming: {times["streaming"]:.4f}s'
        )
