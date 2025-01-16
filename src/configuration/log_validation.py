"""Log validation utilities for JSON log files.

This module provides comprehensive validation functionality for JSON-formatted log files,
including format checking, field validation, type checking, and size limits. It supports
streaming processing for efficient handling of large log files and provides detailed
error reporting with line numbers.
"""

import json
from typing import Any


class LogValidationError(Exception):
    """Base exception class for log validation errors.

    This is the parent class for all log validation-related exceptions,
    providing line number context for error reporting.

    Attributes:
        line_number (Optional[int]): Line number where the error occurred.
        message (str): Detailed error message.
    """

    def __init__(self, message: str, line_number: int = None):
        """Initialize the log validation error.

        Args:
            message: Detailed error description.
            line_number: Optional line number where the error occurred.
        """
        self.line_number = line_number
        super().__init__(f"Line {line_number}: {message}" if line_number else message)


class LogFormatError(LogValidationError):
    """Exception for malformed JSON log entries.

    Raised when a log entry cannot be parsed as valid JSON or has
    structural formatting issues.
    """

    pass


class LogFieldError(LogValidationError):
    """Exception for missing or invalid log fields.

    Raised when required fields are missing or field content does not
    meet validation requirements.
    """

    pass


class LogTypeError(LogValidationError):
    """Exception for incorrect field type errors.

    Raised when a field's value type does not match its expected type
    specification.
    """

    pass


class MaxSizeValidator:
    """Validator for enforcing maximum field sizes in log entries.

    Validates that specified fields in log entries do not exceed their
    defined maximum sizes in characters.

    Attributes:
        max_sizes (Dict[str, int]): Mapping of field names to their maximum
            allowed sizes in characters.
    """

    def __init__(self, max_sizes: dict[str, int] | None) -> None:
        """Initialize the size validator.

        Args:
            max_sizes: Dictionary mapping field names to their maximum
                allowed sizes in characters.

        Example:
            ```python
            validator = MaxSizeValidator({
                "message": 1000,
                "user_id": 50
            })
            ```
        """
        self.max_sizes = max_sizes or {}

    def __call__(self, data: dict[str, Any], line_num: int | None = None) -> None:
        """Validate field sizes in a log entry.

        Args:
            data: Log entry data to validate.
            line_num: Optional line number for error reporting.

        Raises:
            LogValidationError: If any field exceeds its maximum size.

        Example:
            ```python
            validator = MaxSizeValidator({"message": 100})
            validator({"message": "test"}, 1)  # Validates successfully
            ```
        """
        for field, max_size in self.max_sizes.items():
            if field in data and len(str(data[field])) > max_size:
                raise LogValidationError(
                    f"Field '{field}' exceeds maximum size of {max_size} characters",
                    line_num,
                )


def parse_log_line(line: str, line_num: int | None = None) -> dict[str, Any]:
    """Parse a single line of JSON log data.

    Attempts to parse a string as a JSON object, providing line number
    context for error reporting.

    Args:
        line: The log line to parse as JSON.
        line_num: Optional line number for error reporting.

    Returns:
        Dict[str, Any]: Parsed JSON data as a dictionary.

    Raises:
        LogFormatError: If the line cannot be parsed as valid JSON.

    Example:
        ```python
        try:
            data = parse_log_line('{"level": "INFO", "message": "test"}', 1)
            print(data["message"])  # Outputs: test
        except LogFormatError as e:
            print(f"Error at {e.line_number}: {str(e)}")
        ```
    """
    try:
        return json.loads(line)
    except json.JSONDecodeError as e:
        raise LogFormatError(f"Invalid JSON: {e!s}", line_num) from e
    except TypeError as e:
        raise LogFormatError(f"Malformed JSON data: {e!s}", line_num) from e


def validate_log_entry(
    entry: dict[str, Any],
    required_fields: set[str],
    field_types: dict[str, type],
    line_number: int = None,
) -> None:
    """Validate a single log entry against schema requirements.

    Checks that a log entry contains all required fields with correct types.
    Provides detailed error reporting for validation failures.

    Args:
        entry: Log entry dictionary to validate.
        required_fields: Set of field names that must be present.
        field_types: Dictionary mapping field names to their expected types.
        line_number: Optional line number for error reporting.

    Raises:
        LogFieldError: If required fields are missing.
        LogTypeError: If field types don't match specifications.

    Example:
        ```python
        schema = {
            "required": {"timestamp", "level", "message"},
            "types": {
                "timestamp": str,
                "level": str,
                "message": str
            }
        }
        validate_log_entry(
            {"timestamp": "2023-01-01", "level": "INFO", "message": "test"},
            schema["required"],
            schema["types"]
        )
        ```
    """
    # Check required fields
    missing_fields = required_fields - set(entry.keys())
    if missing_fields:
        raise LogFieldError(f"Missing required fields: {', '.join(missing_fields)}", line_number)

    # Check field types
    for field, expected_type in field_types.items():
        if field in entry:
            value = entry[field]
            if not isinstance(value, expected_type):
                raise LogTypeError(
                    f"Field '{field}' has wrong type. Expected {expected_type.__name__}, got {type(value).__name__}",
                    line_number,
                )


def validate_log_file_with_streaming(
    file_path: str,
    required_fields: set[str],
    field_types: dict[str, type],
    chunk_size: int = 8192,
    max_sizes: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    """Validate a JSON log file using memory-efficient streaming.

    Processes and validates a log file in chunks to handle large files
    efficiently. Performs format, field, type, and size validations on
    each log entry.

    Args:
        file_path: Path to the JSON log file to validate.
        required_fields: Set of field names that must be present.
        field_types: Dictionary mapping field names to their expected types.
        chunk_size: Size of chunks to read in bytes (default: 8KB).
        max_sizes: Optional field size limits dictionary.

    Returns:
        List[Dict[str, Any]]: List of validated log entries.

    Raises:
        LogFormatError: For JSON parsing errors.
        LogFieldError: For missing required fields.
        LogTypeError: For incorrect field types.
        LogValidationError: For field size violations.
        IOError: For file reading errors.

    Example:
        ```python
        schema = {
            "required": {"timestamp", "level", "message"},
            "types": {
                "timestamp": str,
                "level": str,
                "message": str
            },
            "max_sizes": {
                "message": 1000
            }
        }

        logs = validate_log_file_with_streaming(
            "app.log",
            schema["required"],
            schema["types"],
            max_sizes=schema["max_sizes"]
        )
        print(f"Validated {len(logs)} log entries")
        ```
    """
    line_num = 0
    buffer = ""
    validated_entries = []
    size_validator = MaxSizeValidator(max_sizes) if max_sizes else None

    try:
        with open(file_path, encoding="utf-8") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                buffer += chunk
                lines = buffer.split("\n")

                # Process all complete lines
                for line in lines[:-1]:
                    line_num += 1
                    if line.strip():  # Skip empty lines
                        try:
                            data = parse_log_line(line, line_num)
                            validate_log_entry(data, required_fields, field_types, line_num)
                            if size_validator:
                                size_validator(data, line_num)
                            validated_entries.append(data)
                        except json.JSONDecodeError as e:
                            raise LogFormatError(f"Invalid JSON: {e!s}", line_num) from e

                # Keep the last partial line
                buffer = lines[-1]

            # Process the last line if it's not empty
            if buffer.strip():
                line_num += 1
                try:
                    data = parse_log_line(buffer, line_num)
                    validate_log_entry(data, required_fields, field_types, line_num)
                    if size_validator:
                        size_validator(data, line_num)
                    validated_entries.append(data)
                except json.JSONDecodeError as e:
                    raise LogFormatError(f"Invalid JSON: {e!s}", line_num) from e

            return validated_entries

    except OSError as e:
        raise LogValidationError(f"Error reading log file: {e!s}")
