"""Shared validation utilities.

This module provides common validation functions and utilities that can be
used across different validation strategies.
"""

from typing import Any, Callable, TypeVar

T = TypeVar("T")


def validate_type(value: Any, expected_type: type | tuple[type, ...], field_name: str) -> list[str]:
    """Validate value is of expected type.

    Args:
        value: Value to validate
        expected_type: Expected type or tuple of types
        field_name: Name of field being validated

    Returns:
        List of validation error messages
    """
    if not isinstance(value, expected_type):
        return [f"{field_name} must be of type {expected_type}, got {type(value)}"]
    return []


def validate_length(
    value: Any,
    field_name: str,
    min_length: int | None = None,
    max_length: int | None = None,
) -> list[str]:
    """Validate length constraints.

    Args:
        value: Value to validate length of
        field_name: Name of field being validated
        min_length: Minimum allowed length
        max_length: Maximum allowed length

    Returns:
        List of validation error messages
    """
    errors = []
    try:
        length = len(value)  # type: ignore
        if min_length is not None and length < min_length:
            errors.append(f"{field_name} length {length} is less than minimum {min_length}")
        if max_length is not None and length > max_length:
            errors.append(f"{field_name} length {length} exceeds maximum {max_length}")
    except TypeError:
        errors.append(f"{field_name} does not support length validation")
    return errors


def validate_range(
    value: Any,
    field_name: str,
    min_value: float | None = None,
    max_value: float | None = None,
) -> list[str]:
    """Validate numeric range constraints.

    Args:
        value: Numeric value to validate
        field_name: Name of field being validated
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        List of validation error messages
    """
    errors = []
    try:
        if min_value is not None and value < min_value:
            errors.append(f"{field_name} value {value} is less than minimum {min_value}")
        if max_value is not None and value > max_value:
            errors.append(f"{field_name} value {value} exceeds maximum {max_value}")
    except TypeError:
        errors.append(f"{field_name} does not support range validation")
    return errors


def validate_with_predicate(
    value: T,
    predicate: Callable[[T], bool],
    error_message: str,
) -> list[str]:
    """Validate value using a predicate function.

    Args:
        value: Value to validate
        predicate: Function that returns True if value is valid
        error_message: Error message if validation fails

    Returns:
        List of validation error messages
    """
    return [] if predicate(value) else [error_message]


def validate_metadata_structure(
    metadata: dict[str, Any],
    required_fields: set[str] | None = None,
    optional_fields: set[str] | None = None,
    max_depth: int | None = None,
) -> list[str]:
    """Validate metadata structure.

    Args:
        metadata: Metadata dictionary to validate
        required_fields: Set of required field names
        optional_fields: Set of optional field names
        max_depth: Maximum allowed nesting depth

    Returns:
        List of validation error messages
    """
    errors = []

    # Validate required fields
    if required_fields:
        missing = required_fields - metadata.keys()
        if missing:
            errors.append(f"Missing required metadata fields: {missing}")

    # Validate no unknown fields
    if optional_fields:
        allowed = required_fields | optional_fields if required_fields else optional_fields
        unknown = metadata.keys() - allowed
        if unknown:
            errors.append(f"Unknown metadata fields: {unknown}")

    # Validate nesting depth
    if max_depth is not None:
        depth = _get_dict_depth(metadata)
        if depth > max_depth:
            errors.append(f"Metadata nesting depth {depth} exceeds maximum {max_depth}")

    return errors


def _get_dict_depth(d: dict[str, Any], current_depth: int = 1) -> int:
    """Get maximum nesting depth of a dictionary.

    Args:
        d: Dictionary to check depth of
        current_depth: Current nesting depth

    Returns:
        Maximum nesting depth
    """
    if not isinstance(d, dict) or not d:
        return current_depth
    return max(
        _get_dict_depth(v, current_depth + 1) if isinstance(v, dict) else current_depth
        for v in d.values()
    )
