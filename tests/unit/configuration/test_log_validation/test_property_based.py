"""Property-based tests for log validation.

Tests:
- Field value properties
- Structure invariants
- Error conditions
- Unicode handling
- Size boundaries
"""
import json
from typing import Any, Dict, List
from hypothesis import given, settings
from hypothesis import strategies as st
from tests.unit.configuration.test_log_validation.conftest import create_test_log_entry, verify_log_structure
from tests.unit.configuration.test_logger_validation import LogFieldError, LogFormatError, LogTypeError, validate_log_entry, validate_log_file

@given(message=st.text(min_size=1), thread_id=st.integers(), extra_fields=st.dictionaries(keys=st.text(min_size=1), values=st.one_of(st.text(), st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.booleans()), max_size=5))
def test_property_valid_entries(message: str, thread_id: int, extra_fields: Dict[str, Any]) -> None:
    """Test that valid entries are always accepted.

    Property: Any entry with correct types and required fields should validate.
    Given: Random valid field values
    When: Entry is validated
    Then: No validation errors should occur
    """
    entry = create_test_log_entry(message, thread_id, **extra_fields)
    validate_log_entry(entry, required_fields={'message', 'thread_id'}, field_types={'message': str, 'thread_id': int})

@given(st.lists(st.dictionaries(keys=st.sampled_from(['message', 'thread_id', 'level', 'extra']), values=st.one_of(st.text(min_size=1), st.integers(), st.lists(st.integers(), max_size=3)), min_size=2), min_size=1, max_size=10))
def test_property_file_validation(entries: List[Dict[str, Any]]) -> None:
    """Test file validation with various entry combinations.

    Property: File validation should handle any combination of valid entries.
    Given: Random list of log entries
    When: File is validated
    Then: Either all entries are valid or first invalid entry is detected
    """
    log_lines = [json.dumps(entry) + '\n' for entry in entries]
    try:
        validated = validate_log_file(log_lines, required_fields={'message', 'thread_id'}, field_types={'message': str, 'thread_id': int})
        assert len(validated) == len(entries)
        for entry in validated:
            verify_log_structure(entry, required_fields={'message', 'thread_id'})
    except (LogFieldError, LogTypeError, LogFormatError):
        pass

@given(st.text(min_size=1).map(lambda s: s + '🚀'), st.integers(min_value=1, max_value=1000))
@settings(deadline=None)
def test_property_unicode_handling(message: str, repeat: int) -> None:
    """Test handling of Unicode characters in messages.

    Property: Unicode characters should be handled correctly at any position.
    Given: Random Unicode message repeated random times
    When: Entry is created and validated
    Then: Unicode content should be preserved
    """
    entry = create_test_log_entry(message * repeat, 123)
    log_line = json.dumps(entry) + '\n'
    validated = validate_log_file([log_line], required_fields={'message', 'thread_id'}, field_types={'message': str, 'thread_id': int})
    assert validated[0]['message'] == message * repeat

@given(st.dictionaries(keys=st.text(min_size=1), values=st.one_of(st.none(), st.booleans(), st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.text(), st.lists(st.integers(), max_size=3), st.dictionaries(keys=st.text(min_size=1), values=st.integers(), max_size=3)), min_size=1, max_size=10))
def test_property_nested_structures(data: Dict[str, Any]) -> None:
    """Test validation of nested data structures.

    Property: Nested structures should be handled consistently.
    Given: Random nested dictionary
    When: Entry is created with nested data
    Then: Validation should handle nested structures appropriately
    """
    entry = {'message': 'Test message', 'thread_id': 123, 'data': data}
    validate_log_entry(entry, required_fields={'message', 'thread_id'}, field_types={'message': str, 'thread_id': int})

@given(message=st.text(min_size=1), thread_id=st.integers(), field_name=st.text(min_size=1).filter(lambda x: x not in {'message', 'thread_id'}), field_value=st.one_of(st.text(), st.integers(), st.floats(allow_nan=False, allow_infinity=False)))
def test_property_extra_fields(message: str, thread_id: int, field_name: str, field_value: Any) -> None:
    """Test handling of additional fields.

    Property: Additional fields should not affect validation of required fields.
    Given: Valid entry with random additional field
    When: Entry is validated
    Then: Validation should succeed regardless of extra field
    """
    entry = create_test_log_entry(message, thread_id, **{field_name: field_value})
    validate_log_entry(entry, required_fields={'message', 'thread_id'}, field_types={'message': str, 'thread_id': int})