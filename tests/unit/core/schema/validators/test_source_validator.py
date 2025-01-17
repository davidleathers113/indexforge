"""Unit tests for source-specific schema validation."""

from typing import Any, Dict

import pytest

from src.core.schema.base import SchemaType, SchemaVersion, ValidationError
from src.core.schema.schema import FieldDefinition, Schema
from src.core.schema.validators.source_validator import SourceValidationRule, SourceValidator


@pytest.fixture
def base_schema() -> Schema:
    """Create a base schema for testing."""
    return Schema(
        name="test_schema",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "content": FieldDefinition(type="string", required=True),
            "timestamp": FieldDefinition(type="string", required=True),
        },
        required_fields={"content", "timestamp"},
    )


@pytest.fixture
def email_validation_rules() -> list[SourceValidationRule]:
    """Create email-specific validation rules for testing."""
    return [
        SourceValidationRule(
            field_name="subject",
            field_type="string",
            required=True,
            constraints={"max_length": 200},
        ),
        SourceValidationRule(
            field_name="recipients",
            field_type="array",
            required=True,
            constraints={"min_length": 1},
        ),
        SourceValidationRule(
            field_name="priority",
            field_type="integer",
            required=False,
            constraints={"min_value": 1, "max_value": 5},
        ),
    ]


def test_source_validator_initialization(
    base_schema: Schema, email_validation_rules: list[SourceValidationRule]
):
    """Test that SourceValidator initializes correctly."""
    validator = SourceValidator("email", base_schema, email_validation_rules)
    assert validator.source_type == "email"
    assert validator.base_schema == base_schema
    assert len(validator.validation_rules) == 3


def test_source_validator_rule_conflict(base_schema: Schema):
    """Test that conflicting rules are detected."""
    conflicting_rules = [
        SourceValidationRule(
            field_name="content",  # Conflicts with base schema
            field_type="string",
            required=True,
        )
    ]
    with pytest.raises(ValueError, match="conflicts with base schema"):
        SourceValidator("email", base_schema, conflicting_rules)


def test_source_validator_validate_success(
    base_schema: Schema, email_validation_rules: list[SourceValidationRule]
):
    """Test successful validation of source-specific fields."""
    validator = SourceValidator("email", base_schema, email_validation_rules)

    valid_data = {
        "content": "Test content",
        "timestamp": "2024-01-01T00:00:00Z",
        "subject": "Test email",
        "recipients": ["user@example.com"],
        "priority": 3,
    }

    errors = validator.validate(valid_data)
    assert not errors, "Expected no validation errors"


def test_source_validator_validate_missing_required(
    base_schema: Schema, email_validation_rules: list[SourceValidationRule]
):
    """Test validation with missing required fields."""
    validator = SourceValidator("email", base_schema, email_validation_rules)

    invalid_data = {
        "content": "Test content",
        "timestamp": "2024-01-01T00:00:00Z",
        # Missing required 'subject' and 'recipients'
    }

    errors = validator.validate(invalid_data)
    assert len(errors) == 2
    error_fields = {e.field for e in errors}
    assert "subject" in error_fields
    assert "recipients" in error_fields


def test_source_validator_validate_type_errors(
    base_schema: Schema, email_validation_rules: list[SourceValidationRule]
):
    """Test validation with incorrect field types."""
    validator = SourceValidator("email", base_schema, email_validation_rules)

    invalid_data = {
        "content": "Test content",
        "timestamp": "2024-01-01T00:00:00Z",
        "subject": "Test email",
        "recipients": "not_a_list",  # Should be array
        "priority": "not_an_integer",  # Should be integer
    }

    errors = validator.validate(invalid_data)
    assert len(errors) == 2
    error_fields = {e.field for e in errors}
    assert "recipients" in error_fields
    assert "priority" in error_fields


def test_source_validator_validate_constraints(
    base_schema: Schema, email_validation_rules: list[SourceValidationRule]
):
    """Test validation of field constraints."""
    validator = SourceValidator("email", base_schema, email_validation_rules)

    invalid_data = {
        "content": "Test content",
        "timestamp": "2024-01-01T00:00:00Z",
        "subject": "T" * 201,  # Exceeds max_length
        "recipients": [],  # Violates min_length
        "priority": 6,  # Exceeds max_value
    }

    errors = validator.validate(invalid_data)
    assert len(errors) == 3
    error_fields = {e.field for e in errors}
    assert "subject" in error_fields
    assert "recipients" in error_fields
    assert "priority" in error_fields


def test_source_validator_custom_error_messages(base_schema: Schema):
    """Test custom error messages in validation rules."""
    rules = [
        SourceValidationRule(
            field_name="custom_field",
            field_type="string",
            required=True,
            error_message="Custom field is required and must be a string",
        )
    ]

    validator = SourceValidator("test", base_schema, rules)
    errors = validator.validate({"content": "test", "timestamp": "2024-01-01T00:00:00Z"})

    assert len(errors) == 1
    assert errors[0].message == "Custom field is required and must be a string"


def test_source_validator_custom_validator(base_schema: Schema):
    """Test custom validator function in constraints."""

    def validate_email(value: str) -> bool:
        return "@" in value and "." in value.split("@")[1]

    rules = [
        SourceValidationRule(
            field_name="email",
            field_type="string",
            required=True,
            constraints={"custom_validator": validate_email},
        )
    ]

    validator = SourceValidator("test", base_schema, rules)

    valid_data = {
        "content": "test",
        "timestamp": "2024-01-01T00:00:00Z",
        "email": "user@example.com",
    }
    assert not validator.validate(valid_data)

    invalid_data = {
        "content": "test",
        "timestamp": "2024-01-01T00:00:00Z",
        "email": "invalid_email",
    }
    errors = validator.validate(invalid_data)
    assert len(errors) == 1
    assert errors[0].field == "email"
