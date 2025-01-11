"""Test basic log validation functionality.

Tests:
- Field presence validation
- Type checking
- Basic JSON structure
- Simple valid cases
"""
import logging
from typing import Any
import pytest
from tests.unit.configuration.test_log_validation.conftest import create_test_log_entry, verify_log_structure
from tests.unit.configuration.test_logger_validation import LogFieldError, LogTypeError, validate_log_entry, validate_log_file

def test_valid_log_entry(json_logger: logging.Logger, temp_log_file: str) -> None:
    """Test validation of a valid log entry.

    Scenario: Create and validate a simple valid log entry
    Given: A logger and a temporary file
    When: A valid log entry is created and validated
    Then: No validation errors should occur
    """
    entry = create_test_log_entry('Test message', 123, timestamp=1234567890)
    verify_log_structure(entry, required_fields={'message', 'thread_id'}, optional_fields={'timestamp'})
    validate_log_entry(entry, required_fields={'message', 'thread_id'}, field_types={'message': str, 'thread_id': int, 'timestamp': int})

def test_field_presence_validation(json_logger: logging.Logger) -> None:
    """Test validation of required fields.

    Scenario: Validate entries with missing required fields
    Given: A set of required fields
    When: Entries are missing some required fields
    Then: Appropriate validation errors should be raised
    """
    required_fields = {'message', 'thread_id', 'level'}
    entry = create_test_log_entry('Test message', 123)
    with pytest.raises(LogFieldError) as exc_info:
        validate_log_entry(entry, required_fields, {})
    assert 'Missing required fields: level' in str(exc_info.value)
    entry = {'message': 'Test'}
    with pytest.raises(LogFieldError) as exc_info:
        validate_log_entry(entry, required_fields, {})
    assert 'thread_id' in str(exc_info.value)
    assert 'level' in str(exc_info.value)

def test_type_validation(json_logger: logging.Logger) -> None:
    """Test validation of field types.

    Scenario: Validate entries with incorrect field types
    Given: A set of field type requirements
    When: Entries have fields of incorrect types
    Then: Type validation errors should be raised
    """
    field_types = {'message': str, 'thread_id': int, 'count': int, 'ratio': float}
    entry = create_test_log_entry(message='Test', thread_id='123', count=5, ratio=0.5)
    with pytest.raises(LogTypeError) as exc_info:
        validate_log_entry(entry, set(), field_types)
    assert 'thread_id' in str(exc_info.value)
    assert 'must be int' in str(exc_info.value)
    entry = create_test_log_entry(message=123, thread_id='123', count='5', ratio='0.5')
    with pytest.raises(LogTypeError) as exc_info:
        validate_log_entry(entry, set(), field_types)
    assert 'message' in str(exc_info.value)

def test_json_structure(write_test_logs: Any, temp_log_file: str) -> None:
    """Test validation of JSON log file structure.

    Scenario: Validate the structure of a JSON log file
    Given: A file with multiple log entries
    When: The file is validated
    Then: All entries should be properly validated
    """
    entries = [create_test_log_entry('Message 1', 1, level='INFO'), create_test_log_entry('Message 2', 2, level='ERROR'), create_test_log_entry('Message 3', 3, level='WARNING')]
    write_test_logs(entries)
    with open(temp_log_file, 'r', encoding='utf-8') as f:
        validated = validate_log_file(f.readlines(), required_fields={'message', 'thread_id', 'level'}, field_types={'message': str, 'thread_id': int, 'level': str})
    assert len(validated) == len(entries)
    for entry, original in zip(validated, entries):
        verify_log_structure(entry, required_fields={'message', 'thread_id', 'level'})