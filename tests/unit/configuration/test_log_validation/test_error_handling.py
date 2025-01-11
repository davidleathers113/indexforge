"""Test error handling and error messages.

Tests:
- Malformed JSON detection
- Missing required fields
- Invalid field types
- Error message formatting
"""
from typing import Any
import pytest
from tests.unit.configuration.test_log_validation.conftest import create_test_log_entry
from tests.unit.configuration.test_logger_validation import LogFieldError, LogFormatError, LogTypeError, validate_log_file

def test_malformed_json(write_test_logs: Any, temp_log_file: str) -> None:
    """Test handling of malformed JSON.

    Scenario: Process a file containing malformed JSON
    Given: A log file with various JSON formatting errors
    When: The file is validated
    Then: Appropriate errors should be raised with line numbers
    """
    with open(temp_log_file, 'w', encoding='utf-8') as f:
        f.write('{"message": "valid", "thread_id": 123}\n')
        f.write('{"message": "incomplete"')
        f.write('{"message": invalid}\n')
        f.write('{"message": "missing comma" "thread_id": 123}\n')
    with pytest.raises(LogFormatError) as exc_info:
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            validate_log_file(f.readlines(), required_fields={'message'}, field_types={'message': str})
    error_msg = str(exc_info.value)
    assert 'Line 2' in error_msg
    assert 'Invalid JSON' in error_msg

def test_missing_required_fields(write_test_logs: Any, temp_log_file: str) -> None:
    """Test handling of missing required fields.

    Scenario: Process entries with missing required fields
    Given: Log entries missing various required fields
    When: The entries are validated
    Then: Clear error messages should indicate missing fields
    """
    entries = [{'message': 'complete', 'thread_id': 123, 'level': 'INFO'}, {'message': 'missing thread_id', 'level': 'INFO'}, {'thread_id': 123, 'level': 'INFO'}, {'other': 'no required fields'}]
    write_test_logs(entries)
    with pytest.raises(LogFieldError) as exc_info:
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            validate_log_file(f.readlines(), required_fields={'message', 'thread_id', 'level'}, field_types={})
    error_msg = str(exc_info.value)
    assert 'Line 2' in error_msg
    assert 'Missing required fields' in error_msg
    assert 'thread_id' in error_msg

def test_invalid_field_types(write_test_logs: Any, temp_log_file: str) -> None:
    """Test handling of invalid field types.

    Scenario: Process entries with incorrect field types
    Given: Log entries with fields of wrong types
    When: The entries are validated
    Then: Error messages should clearly indicate type mismatches
    """
    entries = [create_test_log_entry('valid', 123), create_test_log_entry(123, 'invalid'), create_test_log_entry('valid', 3.14)]
    write_test_logs(entries)
    with pytest.raises(LogTypeError) as exc_info:
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            validate_log_file(f.readlines(), required_fields={'message', 'thread_id'}, field_types={'message': str, 'thread_id': int})
    error_msg = str(exc_info.value)
    assert 'Line 2' in error_msg
    assert 'must be' in error_msg
    assert 'got' in error_msg

def test_error_message_formatting() -> None:
    """Test formatting of error messages.

    Scenario: Generate various validation errors
    Given: Different types of validation failures
    When: Errors are raised
    Then: Error messages should be clear and include context
    """
    with pytest.raises(LogFieldError) as exc_info:
        validate_log_file(['{"msg": "wrong field name"}\n'], required_fields={'message'}, field_types={})
    assert 'Line 1' in str(exc_info.value)
    assert 'message' in str(exc_info.value)
    with pytest.raises(LogTypeError) as exc_info:
        validate_log_file(['{"message": 123}\n'], required_fields={'message'}, field_types={'message': str})
    assert 'Line 1' in str(exc_info.value)
    assert 'must be str' in str(exc_info.value)
    assert 'got int' in str(exc_info.value)
    with pytest.raises(LogFormatError) as exc_info:
        validate_log_file(['{"invalid": json"}\n'], required_fields={}, field_types={})
    assert 'Line 1' in str(exc_info.value)
    assert 'Invalid JSON' in str(exc_info.value)