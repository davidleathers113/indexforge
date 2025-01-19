"""Source-specific schema validation.

This module provides validation functionality for source-specific schema requirements,
including custom field validation, source-type validation, and specialized rules.
"""

from typing import Any

from pydantic import BaseModel, Field

from src.core.schema.base import ValidationError
from src.core.schema.schema import Schema


class SourceValidationRule(BaseModel):
    """Definition of a source-specific validation rule."""

    field_name: str = Field(..., description="Name of the field to validate")
    field_type: str = Field(..., description="Expected type of the field")
    required: bool = Field(default=False, description="Whether the field is required")
    constraints: dict[str, Any] = Field(
        default_factory=dict, description="Additional validation constraints"
    )
    error_message: str = Field(
        default="", description="Custom error message for validation failures"
    )


class SourceValidator:
    """Validator for source-specific schema requirements."""

    def __init__(
        self,
        source_type: str,
        base_schema: Schema,
        validation_rules: list[SourceValidationRule] | None = None,
    ):
        """Initialize source validator.

        Args:
            source_type: Type of source (e.g., 'email', 'pdf', etc.)
            base_schema: Base schema to extend with source-specific validation
            validation_rules: Optional list of source-specific validation rules
        """
        self.source_type = source_type
        self.base_schema = base_schema
        self.validation_rules = validation_rules or []
        self._validate_rules()

    def _validate_rules(self) -> None:
        """Validate that rules don't conflict with base schema."""
        base_fields = set(self.base_schema.fields.keys())
        for rule in self.validation_rules:
            if rule.field_name in base_fields:
                raise ValueError(
                    f"Validation rule for {rule.field_name} conflicts with base schema"
                )

    def validate(self, data: dict[str, Any]) -> list[ValidationError]:
        """Validate data against source-specific rules.

        Args:
            data: The data to validate

        Returns:
            List of validation errors, empty if validation succeeds
        """
        errors = []

        # First validate against base schema
        errors.extend(self.base_schema.validate(data))

        # Then validate source-specific rules
        for rule in self.validation_rules:
            if rule.required and rule.field_name not in data:
                errors.append(
                    ValidationError(
                        message=rule.error_message or f"Missing required field: {rule.field_name}",
                        field=rule.field_name,
                    )
                )
                continue

            if rule.field_name in data:
                value = data[rule.field_name]
                try:
                    self._validate_field_type(value, rule.field_type, rule.field_name)
                    self._validate_constraints(value, rule.constraints, rule.field_name)
                except ValidationError as e:
                    if rule.error_message:
                        e.message = rule.error_message
                    errors.append(e)

        return errors

    def _validate_field_type(self, value: Any, expected_type: str, field_name: str) -> None:
        """Validate field type.

        Args:
            value: Value to validate
            expected_type: Expected type name
            field_name: Name of the field being validated

        Raises:
            ValidationError: If type validation fails
        """
        type_map = {
            "string": str,
            "integer": int,
            "float": float,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }

        if expected_type not in type_map:
            return  # Custom types are validated by constraints

        expected_python_type = type_map[expected_type]
        if not isinstance(value, expected_python_type):
            raise ValidationError(
                f"Invalid type for field {field_name}. Expected {expected_type}",
                field=field_name,
                details={"expected_type": expected_type, "actual_type": type(value).__name__},
            )

    def _validate_constraints(
        self, value: Any, constraints: dict[str, Any], field_name: str
    ) -> None:
        """Validate field constraints.

        Args:
            value: Value to validate
            constraints: Dictionary of constraints to check
            field_name: Name of the field being validated

        Raises:
            ValidationError: If constraint validation fails
        """
        for constraint, constraint_value in constraints.items():
            if not self._check_constraint(value, constraint, constraint_value):
                raise ValidationError(
                    f"Constraint violation for field {field_name}: {constraint}",
                    field=field_name,
                    details={"constraint": constraint, "value": constraint_value},
                )

    def _check_constraint(self, value: Any, constraint: str, constraint_value: Any) -> bool:
        """Check if value satisfies a constraint.

        Args:
            value: Value to check
            constraint: Constraint name
            constraint_value: Constraint parameters

        Returns:
            True if constraint is satisfied, False otherwise
        """
        if constraint == "min_length" and isinstance(value, (str, list)):
            return len(value) >= constraint_value
        elif constraint == "max_length" and isinstance(value, (str, list)):
            return len(value) <= constraint_value
        elif constraint == "pattern" and isinstance(value, str):
            import re

            return bool(re.match(constraint_value, value))
        elif constraint == "min_value" and isinstance(value, (int, float)):
            return value >= constraint_value
        elif constraint == "max_value" and isinstance(value, (int, float)):
            return value <= constraint_value
        elif constraint == "allowed_values":
            return value in constraint_value
        elif constraint == "custom_validator" and callable(constraint_value):
            return constraint_value(value)
        return True  # Unknown constraints are ignored
