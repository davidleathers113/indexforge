"""Concrete schema implementation for IndexForge.

This module provides the core schema implementation with validation,
compatibility checking, and serialization support.
"""

import re
from typing import Any, Dict, Iterator, List, Optional, Set

from pydantic import BaseModel, Field

from src.core.schema.base import (
    BaseSchema,
    SchemaType,
    SchemaValidator,
    SchemaVersion,
    ValidationError,
)


class FieldDefinition(BaseModel):
    """Definition of a schema field."""

    type: str = Field(..., description="Field data type")
    description: str = Field(default="", description="Field description")
    required: bool = Field(default=False, description="Whether field is required")
    default: Optional[Any] = Field(default=None, description="Default field value")
    constraints: Dict[str, Any] = Field(
        default_factory=dict, description="Additional field constraints"
    )
    override: bool = Field(default=False, description="Whether this field overrides a parent field")


class Schema(BaseSchema):
    """Concrete schema implementation with validation support."""

    def __init__(
        self,
        name: str,
        version: SchemaVersion,
        schema_type: SchemaType,
        fields: Dict[str, FieldDefinition],
        required_fields: Optional[Set[str]] = None,
        validators: Optional[List[SchemaValidator]] = None,
        description: str = "",
        parent_schema: Optional["Schema"] = None,
    ):
        """Initialize schema.

        Args:
            name: Unique name identifying the schema
            version: Schema version information
            schema_type: Type of schema (document, chunk, etc.)
            fields: Dictionary of field definitions
            required_fields: Set of required field names
            validators: List of custom validators
            description: Schema description
            parent_schema: Optional parent schema for inheritance
        """
        self.parent_schema = parent_schema
        merged_fields = self._merge_parent_fields(fields)
        merged_required = (required_fields or set()) | (
            parent_schema.required_fields if parent_schema else set()
        )

        super().__init__(
            name=name,
            version=version,
            schema_type=schema_type,
            fields=merged_fields,
            required_fields=merged_required,
            validators=validators,
            description=description,
        )
        self._validate_field_definitions()

    def _merge_parent_fields(
        self, fields: Dict[str, FieldDefinition]
    ) -> Dict[str, FieldDefinition]:
        """Merge fields with parent schema fields, handling overrides.

        Args:
            fields: Dictionary of field definitions for this schema

        Returns:
            Merged dictionary of field definitions
        """
        if not self.parent_schema:
            return fields

        merged = {}
        # Copy parent fields first
        for name, field in self.parent_schema.fields.items():
            merged[name] = field

        # Override or add child fields
        for name, field in fields.items():
            if name in merged and not field.override:
                raise ValueError(
                    f"Field {name} already defined in parent schema. Use override=True to override."
                )
            merged[name] = field

        return merged

    def get_all_fields(self) -> Iterator[tuple[str, FieldDefinition, bool]]:
        """Get all fields including inherited ones.

        Yields:
            Tuples of (field_name, field_definition, is_inherited)
        """
        parent_fields = set()
        if self.parent_schema:
            for name, field, _ in self.parent_schema.get_all_fields():
                if name not in self.fields or not self.fields[name].override:
                    parent_fields.add(name)
                    yield name, field, True

        for name, field in self.fields.items():
            yield name, field, name in parent_fields

    def _validate_field_definitions(self) -> None:
        """Validate field definitions for consistency."""
        for field_name, field_def in self.fields.items():
            if not isinstance(field_def, FieldDefinition):
                if isinstance(field_def, dict):
                    self.fields[field_name] = FieldDefinition(**field_def)
                else:
                    raise ValueError(
                        f"Field definition for {field_name} must be FieldDefinition or dict"
                    )

    def validate(self, data: Dict[str, Any]) -> List[ValidationError]:
        """Validate data against this schema.

        Args:
            data: The data to validate

        Returns:
            List of validation errors, empty if validation succeeds
        """
        errors: List[ValidationError] = []

        # Check required fields
        for field in self.required_fields:
            if field not in data:
                errors.append(
                    ValidationError(
                        f"Missing required field: {field}",
                        field=field,
                    )
                )

        # Validate field types and constraints
        for field_name, value in data.items():
            if field_name not in self.fields:
                errors.append(
                    ValidationError(
                        f"Unknown field: {field_name}",
                        field=field_name,
                    )
                )
                continue

            field_def = self.fields[field_name]
            try:
                self._validate_field(field_name, value, field_def)
            except ValidationError as e:
                errors.append(e)

        # Run custom validators
        for validator in self.validators:
            errors.extend(validator.validate(data))

        # Run parent schema validation if exists
        if self.parent_schema:
            errors.extend(self.parent_schema.validate(data))

        return errors

    def _validate_field(self, field_name: str, value: Any, field_def: FieldDefinition) -> None:
        """Validate a single field value.

        Args:
            field_name: Name of the field
            value: Field value to validate
            field_def: Field definition

        Raises:
            ValidationError: If validation fails
        """
        # Type validation
        expected_type = field_def.type
        if not self._check_type(value, expected_type):
            raise ValidationError(
                f"Invalid type for field {field_name}. Expected {expected_type}",
                field=field_name,
                details={"expected_type": expected_type, "actual_type": type(value).__name__},
            )

        # Constraint validation
        for constraint, constraint_value in field_def.constraints.items():
            if not self._check_constraint(value, constraint, constraint_value):
                raise ValidationError(
                    f"Constraint violation for field {field_name}: {constraint}",
                    field=field_name,
                    details={"constraint": constraint, "value": constraint_value},
                )

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type.

        Args:
            value: Value to check
            expected_type: Expected type name

        Returns:
            True if type matches, False otherwise
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
            return True  # Custom types are validated by validators

        return isinstance(value, type_map[expected_type])

    def _check_constraint(self, value: Any, constraint: str, constraint_value: Any) -> bool:
        """Check if value satisfies a constraint.

        Args:
            value: Value to check
            constraint: Constraint name
            constraint_value: Constraint parameters

        Returns:
            True if constraint is satisfied, False otherwise
        """
        if constraint == "min":
            return value >= constraint_value
        elif constraint == "max":
            return value <= constraint_value
        elif constraint == "pattern":
            return bool(re.match(constraint_value, str(value)))
        elif constraint == "enum":
            return value in constraint_value
        return True  # Unknown constraints are ignored

    def is_compatible(self, other: BaseSchema) -> bool:
        """Check if this schema is compatible with another schema.

        Args:
            other: Another schema to check compatibility with

        Returns:
            True if schemas are compatible, False otherwise
        """
        if not isinstance(other, Schema):
            return False

        if self.schema_type != other.schema_type:
            return False

        # Check version compatibility
        if other.version < self.version and self.version.is_breaking_change:
            return False

        # Check field compatibility
        for field_name, field_def in self.fields.items():
            if field_name in other.fields:
                other_field = other.fields[field_name]
                if field_def.type != other_field.type:
                    return False
                if field_def.required and not other_field.required:
                    return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary representation.

        Returns:
            Dictionary representation of the schema
        """
        return {
            "name": self.name,
            "version": self.version.dict(),
            "schema_type": self.schema_type.value,
            "fields": {name: field_def.dict() for name, field_def in self.fields.items()},
            "required_fields": list(self.required_fields),
            "description": self.description,
            "parent_schema": self.parent_schema.to_dict() if self.parent_schema else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Schema":
        """Create schema instance from dictionary representation.

        Args:
            data: Dictionary representation of schema

        Returns:
            Schema instance
        """
        parent_data = data.pop("parent_schema", None)
        parent_schema = cls.from_dict(parent_data) if parent_data else None

        version_data = data.pop("version")
        version = SchemaVersion(**version_data)

        schema_type = SchemaType(data.pop("schema_type"))

        fields = {
            name: FieldDefinition(**field_def) for name, field_def in data.pop("fields").items()
        }

        required_fields = set(data.pop("required_fields", []))

        return cls(
            version=version,
            schema_type=schema_type,
            fields=fields,
            required_fields=required_fields,
            parent_schema=parent_schema,
            **data,
        )
