"""Unit tests for schema implementation."""


from src.core.schema.base import SchemaType, SchemaVersion
from src.core.schema.schema import FieldDefinition, Schema


def test_schema_version_comparison():
    """Test schema version comparison logic."""
    v1 = SchemaVersion(major=1, minor=0, patch=0)
    v2 = SchemaVersion(major=1, minor=1, patch=0)
    v3 = SchemaVersion(major=2, minor=0, patch=0)

    assert v1 < v2
    assert v2 < v3
    assert v1 < v3
    assert v3.is_breaking_change
    assert not v1.is_breaking_change


def test_field_definition():
    """Test field definition creation and validation."""
    field = FieldDefinition(
        type="string", description="Test field", required=True, constraints={"pattern": r"^test.*$"}
    )

    assert field.type == "string"
    assert field.required
    assert "pattern" in field.constraints


def test_schema_validation():
    """Test schema validation functionality."""
    schema = Schema(
        name="test_schema",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "title": FieldDefinition(
                type="string", required=True, constraints={"pattern": r"^[A-Z].*$"}
            ),
            "count": FieldDefinition(type="integer", constraints={"min": 0, "max": 100}),
        },
        required_fields={"title"},
        description="Test schema",
    )

    # Valid data
    valid_data = {"title": "Test title", "count": 50}
    assert not schema.validate(valid_data)

    # Missing required field
    invalid_data1 = {"count": 50}
    errors = schema.validate(invalid_data1)
    assert len(errors) == 1
    assert "Missing required field: title" in str(errors[0])

    # Invalid type
    invalid_data2 = {"title": "Test", "count": "50"}  # Should be integer
    errors = schema.validate(invalid_data2)
    assert len(errors) == 1
    assert "Invalid type for field count" in str(errors[0])

    # Invalid constraint
    invalid_data3 = {"title": "test", "count": 50}  # Should start with uppercase
    errors = schema.validate(invalid_data3)
    assert len(errors) == 1
    assert "Constraint violation" in str(errors[0])


def test_schema_compatibility():
    """Test schema compatibility checking."""
    base_schema = Schema(
        name="base",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "title": FieldDefinition(type="string", required=True),
            "description": FieldDefinition(type="string"),
        },
        required_fields={"title"},
    )

    # Compatible schema (adds optional field)
    compatible_schema = Schema(
        name="compatible",
        version=SchemaVersion(major=1, minor=1, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "title": FieldDefinition(type="string", required=True),
            "description": FieldDefinition(type="string"),
            "tags": FieldDefinition(type="array"),
        },
        required_fields={"title"},
    )

    # Incompatible schema (changes required field type)
    incompatible_schema = Schema(
        name="incompatible",
        version=SchemaVersion(major=2, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "title": FieldDefinition(type="integer", required=True),
            "description": FieldDefinition(type="string"),
        },
        required_fields={"title"},
    )

    assert base_schema.is_compatible(compatible_schema)
    assert not base_schema.is_compatible(incompatible_schema)


def test_schema_serialization():
    """Test schema serialization and deserialization."""
    original_schema = Schema(
        name="test",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "title": FieldDefinition(type="string", required=True, description="Document title")
        },
        required_fields={"title"},
        description="Test schema",
    )

    # Convert to dict and back
    schema_dict = original_schema.to_dict()
    restored_schema = Schema.from_dict(schema_dict)

    assert restored_schema.name == original_schema.name
    assert restored_schema.version.major == original_schema.version.major
    assert restored_schema.schema_type == original_schema.schema_type
    assert restored_schema.fields["title"].type == original_schema.fields["title"].type
    assert restored_schema.required_fields == original_schema.required_fields


def test_schema_inheritance():
    """Test schema inheritance functionality."""
    parent_schema = Schema(
        name="parent",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "id": FieldDefinition(type="string", required=True),
            "created_at": FieldDefinition(type="string"),
        },
        required_fields={"id"},
    )

    child_schema = Schema(
        name="child",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={"title": FieldDefinition(type="string", required=True)},
        required_fields={"title"},
        parent_schema=parent_schema,
    )

    # Should validate against both child and parent fields
    valid_data = {"id": "123", "title": "Test", "created_at": "2024-01-01"}
    assert not child_schema.validate(valid_data)

    # Should fail if missing parent required field
    invalid_data = {"title": "Test", "created_at": "2024-01-01"}
    errors = child_schema.validate(invalid_data)
    assert len(errors) == 1
    assert "Missing required field: id" in str(errors[0])
