import tracemalloc
'Test concurrent logging operations.\n\nTests:\n- Multi-threaded logging\n- Race conditions\n- Thread ID tracking\n- Log ordering\n- Thread safety of validation\n'
import logging
import threading
import time
from typing import Any, Dict, List, Set
import pytest
from tests.unit.configuration.test_log_validation.conftest import create_test_log_entry, verify_log_structure
from tests.unit.configuration.test_logger_validation import LogTypeError, validate_log_file

def test_concurrent_logging(json_logger: logging.Logger, temp_log_file: str) -> None:
    """Test logging from multiple threads.

    Scenario: Multiple threads writing log entries simultaneously
    Given: A JSON logger and multiple threads
    When: All threads log messages concurrently
    Then: All messages should be properly logged and validated
    """
    thread_count = 3
    messages_per_thread = 10

    def log_messages() -> None:
        thread_id = threading.get_ident()
        for i in range(messages_per_thread):
            json_logger.info('Message %d from thread %d', i, thread_id, extra={'thread_id': thread_id, 'sequence': i})
            time.sleep(0.001)
    threads = [threading.Thread(target=log_messages) for _ in range(thread_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    with open(temp_log_file, 'r', encoding='utf-8') as f:
        log_lines = f.readlines()
        expected_count = thread_count * messages_per_thread
        assert len(log_lines) == expected_count, f'Expected {expected_count} log entries, got {len(log_lines)}'
        validated = validate_log_file(log_lines, required_fields={'message', 'thread_id', 'sequence'}, field_types={'message': str, 'thread_id': int, 'sequence': int})
        thread_ids = {entry['thread_id'] for entry in validated}
        assert len(thread_ids) == thread_count, f'Expected {thread_count} unique thread IDs, got {len(thread_ids)}'
        for thread_id in thread_ids:
            thread_messages = [entry for entry in validated if entry['thread_id'] == thread_id]
            sequences = {entry['sequence'] for entry in thread_messages}
            assert sequences == set(range(messages_per_thread)), f'Missing sequences for thread {thread_id}'

def test_concurrent_validation(write_test_logs: Any, temp_log_file: str) -> None:
    """Test concurrent validation of log entries.

    Scenario: Multiple threads validating the same log file
    Given: A log file with multiple entries
    When: Multiple threads validate the file concurrently
    Then: All validations should complete successfully
    """
    entries = [create_test_log_entry(f'Message {i}', i) for i in range(100)]
    write_test_logs(entries)

    def validate_logs() -> None:
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            validated = validate_log_file(f.readlines(), required_fields={'message', 'thread_id'}, field_types={'message': str, 'thread_id': int})
            assert len(validated) == len(entries)
    threads = [threading.Thread(target=validate_logs) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

def test_log_ordering(json_logger: logging.Logger, temp_log_file: str) -> None:
    """Test ordering of log entries from multiple threads.

    Scenario: Multiple threads logging with timestamps
    Given: Multiple threads logging timestamped messages
    When: Messages are logged concurrently
    Then: Timestamps should be monotonically increasing
    """

    def log_with_timestamp() -> None:
        for _ in range(5):
            timestamp = time.time()
            json_logger.info('Timestamped message', extra={'thread_id': threading.get_ident(), 'timestamp': timestamp})
            time.sleep(0.01)
    threads = [threading.Thread(target=log_with_timestamp) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    with open(temp_log_file, 'r', encoding='utf-8') as f:
        validated = validate_log_file(f.readlines(), required_fields={'message', 'thread_id', 'timestamp'}, field_types={'message': str, 'thread_id': int, 'timestamp': float})
        timestamps = [entry['timestamp'] for entry in validated]
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i - 1], f'Timestamps not monotonically increasing at index {i}'

def test_concurrent_error_handling(json_logger: logging.Logger, temp_log_file: str) -> None:
    """Test error handling during concurrent logging.

    Scenario: Multiple threads logging with some invalid entries
    Given: Multiple threads logging valid and invalid messages
    When: Messages are logged concurrently
    Then: Invalid entries should be properly detected and reported
    """

    def log_mixed_messages(include_invalid: bool) -> None:
        thread_id = threading.get_ident()
        for i in range(5):
            if include_invalid and i % 2 == 0:
                json_logger.info('Invalid message %d', i, extra={'thread_id': str(thread_id)})
            else:
                json_logger.info('Valid message %d', i, extra={'thread_id': thread_id})
            time.sleep(0.001)
    threads = [threading.Thread(target=log_mixed_messages, args=(i % 2 == 0,)) for i in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    with pytest.raises(LogTypeError) as exc_info:
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            validate_log_file(f.readlines(), required_fields={'message', 'thread_id'}, field_types={'message': str, 'thread_id': int})
    error_msg = str(exc_info.value)
    assert 'thread_id' in error_msg
    assert 'must be int' in error_msg