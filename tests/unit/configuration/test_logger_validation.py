"""Validation utilities for logger tests."""
import json
from typing import Any

from hypothesis import given, strategies as st
import pytest


class LogValidationError(Exception):
    """Base class for log validation errors."""

    def __init__(self, message: str, line_num: int | None = None) -> None:
        self.line_num = line_num
        if line_num is not None:
            message = f'Line {line_num}: {message}'
        super().__init__(message)


class LogFormatError(LogValidationError):
    """Error for malformed log entries."""
    pass


class LogFieldError(LogValidationError):
    """Error for missing or invalid fields."""
    pass


class LogTypeError(LogValidationError):
    """Error for incorrect field types."""
    pass


def validate_log_entry(data: dict[str, Any], required_fields: set[str], field_types: dict[str, type], line_num: int | None = None) -> None:
    """Validate a single log entry.

    Thread-safe implementation for validating log entries, ensuring consistent
    error detection and reporting in concurrent scenarios.

    Args:
        data: The log entry to validate
        required_fields: Set of field names that must be present
        field_types: Dictionary mapping field names to their expected types
        line_num: Optional line number for error reporting

    Raises:
        LogFieldError: If a required field is missing
        LogTypeError: If a field has an incorrect type
    """
    try:
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise LogFieldError('Missing required fields: %s' % ', '.join(sorted(missing_fields)), line_num)
        for field, expected_type in field_types.items():
            if field in data and (not isinstance(data[field], expected_type)):
                raise LogTypeError("Field '%s' must be %s, got %s" % (field, expected_type.__name__, type(data[field]).__name__), line_num)
    except (LogFieldError, LogTypeError) as e:
        if line_num is not None and (not hasattr(e, 'line_num')):
            e.line_num = line_num
        raise


def parse_log_line(line: str, line_num: int | None = None) -> dict[str, Any]:
    """Parse a single log line as JSON.

    Args:
        line: The log line to parse
        line_num: Optional line number for error reporting

    Returns:
        The parsed JSON data

    Raises:
        LogFormatError: If the line cannot be parsed as JSON
    """
    try:
        return json.loads(line)
    except json.JSONDecodeError as e:
        raise LogFormatError(f'Invalid JSON: {e!s}', line_num) from e
    except TypeError as e:
        raise LogFormatError(f'Malformed JSON data: {e!s}', line_num) from e


def validate_log_file(log_lines: list[str], required_fields: set[str], field_types: dict[str, type]) -> list[dict[str, Any]]:
    """Validate all entries in a log file.

    Args:
        log_lines: List of log lines to validate
        required_fields: Set of field names that must be present
        field_types: Dictionary mapping field names to their expected types

    Returns:
        List of validated log entries

    Raises:
        LogFormatError: If any line cannot be parsed as JSON
        LogFieldError: If any required fields are missing
        LogTypeError: If any fields have incorrect types
        ValueError: If the log file is empty
    """
    if not log_lines:
        raise ValueError('Log file is empty')
    validated_entries = []
    for i, line in enumerate(log_lines, 1):
        data = parse_log_line(line, i)
        validate_log_entry(data, required_fields, field_types, i)
        validated_entries.append(data)
    return validated_entries


@given(message=st.text(min_size=1), thread_id=st.integers(), extra_fields=st.dictionaries(keys=st.text(min_size=1), values=st.one_of(st.text(), st.integers(), st.floats(allow_nan=False)), max_size=5))
def test_property_validate_log_entry(message: str, thread_id: int, extra_fields: dict[str, Any]) -> None:
    """Property-based test for log entry validation.

    Tests that valid entries are accepted and invalid ones are rejected.
    """
    log_entry = {'message': message, 'thread_id': thread_id, **extra_fields}
    validate_log_entry(log_entry, required_fields={'message', 'thread_id'}, field_types={'message': str, 'thread_id': int})
    invalid_entry = log_entry.copy()
    del invalid_entry['message']
    with pytest.raises(LogFieldError) as exc_info:
        validate_log_entry(invalid_entry, required_fields={'message', 'thread_id'}, field_types={'message': str, 'thread_id': int})
    assert 'Missing required fields: message' in str(exc_info.value)
    invalid_entry = log_entry.copy()
    invalid_entry['thread_id'] = str(thread_id)
    with pytest.raises(LogTypeError) as exc_info:
        validate_log_entry(invalid_entry, required_fields={'message', 'thread_id'}, field_types={'message': str, 'thread_id': int})
    assert "Field 'thread_id' must be int" in str(exc_info.value)


@given(st.lists(st.dictionaries(keys=st.sampled_from(['message', 'thread_id', 'extra']), values=st.one_of(st.text(min_size=1), st.integers(), st.lists(st.integers(), max_size=3)), min_size=2), min_size=1, max_size=10))
def test_property_nested_json(entries: list[dict[str, Any]]) -> None:
    """Property-based test for nested JSON structures."""
    log_lines = [json.dumps(entry) + '\n' for entry in entries]
    try:
        validated = validate_log_file(log_lines, required_fields={'message', 'thread_id'}, field_types={'message': str, 'thread_id': int})
    except (LogFieldError, LogTypeError, LogFormatError):
        pass
    else:
        assert len(validated) == len(entries)
        for entry in validated:
            assert isinstance(entry['message'], str)
            assert isinstance(entry['thread_id'], int)


@given(st.text(min_size=1).map(lambda s: s + '🚀'), st.integers(min_value=1, max_value=1000000))
def test_property_unicode_handling(message: str, size: int) -> None:
    """Property-based test for Unicode handling in log messages."""
    log_entry = {'message': message * size, 'size': size}
    log_line = json.dumps(log_entry) + '\n'
    validated = validate_log_file([log_line], required_fields={'message', 'size'}, field_types={'message': str, 'size': int})
    assert validated[0]['message'] == message * size
    assert validated[0]['size'] == size


class MaxSizeValidator:
    """Validator for maximum field sizes."""

    def __init__(self, max_sizes: dict[str, int]) -> None:
        self.max_sizes = max_sizes

    def __call__(self, data: dict[str, Any], line_num: int | None = None) -> None:
        """Validate field sizes."""
        for field, max_size in self.max_sizes.items():
            if field in data and len(str(data[field])) > max_size:
                raise LogValidationError(f"Field '{field}' exceeds maximum size of {max_size} characters", line_num)


def validate_log_file_with_streaming(log_file_path: str, required_fields: set[str], field_types: dict[str, type], chunk_size: int = 8192, max_sizes: dict[str, int] | None = None) -> list[dict[str, Any]]:
    """Validate a log file using streaming to handle large files efficiently.

    Args:
        log_file_path: Path to the log file
        required_fields: Set of field names that must be present
        field_types: Dictionary mapping field names to their expected types
        chunk_size: Size of chunks to read (default: 8KB)
        max_sizes: Optional dictionary mapping field names to maximum sizes

    Returns:
        List of validated log entries

    Raises:
        LogFormatError: If any line cannot be parsed as JSON
        LogFieldError: If any required fields are missing
        LogTypeError: If any fields have incorrect types
        LogValidationError: If any field size limits are exceeded
        IOError: If the file cannot be read
    """
    line_num = 0
    buffer = ''
    validated_entries = []
    size_validator = MaxSizeValidator(max_sizes) if max_sizes else None
    try:
        with open(log_file_path, encoding='utf-8') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                buffer += chunk
                lines = buffer.split('\n')
                for line in lines[:-1]:
                    line_num += 1
                    if line.strip():
                        data = parse_log_line(line, line_num)
                        validate_log_entry(data, required_fields, field_types, line_num)
                        if size_validator:
                            size_validator(data, line_num)
                        validated_entries.append(data)
                buffer = lines[-1]
            if buffer.strip():
                line_num += 1
                data = parse_log_line(buffer, line_num)
                validate_log_entry(data, required_fields, field_types, line_num)
                if size_validator:
                    size_validator(data, line_num)
                validated_entries.append(data)
            return validated_entries
    except OSError as e:
        raise LogValidationError(f'Error reading log file: {e!s}')