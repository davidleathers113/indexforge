"""Unit tests for schema storage implementation."""

import json

import pytest

from src.core.schema.base import SchemaType, SchemaVersion
from src.core.schema.schema import FieldDefinition, Schema
from src.core.schema.storage import SchemaStorage


@pytest.fixture
def temp_storage_dir(tmp_path):
    """Create temporary storage directory."""
    storage_dir = tmp_path / "schemas"
    storage_dir.mkdir()
    return storage_dir


@pytest.fixture
def test_schema():
    """Create test schema."""
    return Schema(
        name="test_schema",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "title": FieldDefinition(type="string", required=True),
            "count": FieldDefinition(type="integer"),
        },
        required_fields={"title"},
        description="Test schema",
    )


def test_schema_storage_initialization(temp_storage_dir):
    """Test schema storage initialization."""
    storage = SchemaStorage(temp_storage_dir)
    assert storage.storage_dir.exists()
    assert storage.storage_dir == temp_storage_dir


def test_store_and_retrieve_schema(temp_storage_dir, test_schema):
    """Test storing and retrieving a schema."""
    storage = SchemaStorage(temp_storage_dir)

    # Store schema
    storage.store_schema(test_schema)

    # Verify file exists
    schema_path = temp_storage_dir / "test_schema_1.0.0.json"
    assert schema_path.exists()

    # Verify file contents
    with open(schema_path) as f:
        data = json.load(f)
        assert data["metadata"]["name"] == "test_schema"
        assert data["metadata"]["version"]["major"] == 1
        assert data["metadata"]["is_active"] is True

    # Retrieve schema
    retrieved_schema = storage.get_schema("test_schema")
    assert retrieved_schema is not None
    assert retrieved_schema.name == test_schema.name
    assert retrieved_schema.version == test_schema.version
    assert retrieved_schema.fields["title"].type == "string"


def test_schema_versioning(temp_storage_dir, test_schema):
    """Test schema versioning functionality."""
    storage = SchemaStorage(temp_storage_dir)

    # Store v1
    storage.store_schema(test_schema)

    # Create and store v2
    v2_schema = Schema(
        name="test_schema",
        version=SchemaVersion(major=1, minor=1, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "title": FieldDefinition(type="string", required=True),
            "count": FieldDefinition(type="integer"),
            "tags": FieldDefinition(type="array"),
        },
        required_fields={"title"},
        description="Test schema v2",
    )
    storage.store_schema(v2_schema)

    # Get versions
    versions = storage.get_schema_versions("test_schema")
    assert len(versions) == 2
    assert versions[0].minor == 1  # Latest first
    assert versions[1].minor == 0

    # Get specific version
    v1 = storage.get_schema("test_schema", SchemaVersion(major=1, minor=0, patch=0))
    assert v1 is not None
    assert len(v1.fields) == 2

    # Get active version (should be v2)
    active = storage.get_schema("test_schema")
    assert active is not None
    assert active.version.minor == 1
    assert len(active.fields) == 3


def test_schema_listing(temp_storage_dir, test_schema):
    """Test listing available schemas."""
    storage = SchemaStorage(temp_storage_dir)

    # Store document schema
    storage.store_schema(test_schema)

    # Store chunk schema
    chunk_schema = Schema(
        name="test_chunk",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.CHUNK,
        fields={
            "content": FieldDefinition(type="string", required=True),
        },
        required_fields={"content"},
        description="Test chunk schema",
    )
    storage.store_schema(chunk_schema)

    # List all schemas
    schemas = storage.list_schemas()
    assert len(schemas) == 2

    # List by type
    doc_schemas = storage.list_schemas(SchemaType.DOCUMENT)
    assert len(doc_schemas) == 1
    assert doc_schemas[0].name == "test_schema"

    chunk_schemas = storage.list_schemas(SchemaType.CHUNK)
    assert len(chunk_schemas) == 1
    assert chunk_schemas[0].name == "test_chunk"


def test_schema_deletion(temp_storage_dir, test_schema):
    """Test schema deletion functionality."""
    storage = SchemaStorage(temp_storage_dir)

    # Store schema
    storage.store_schema(test_schema)
    assert storage.get_schema("test_schema") is not None

    # Delete schema
    assert storage.delete_schema("test_schema") is True
    assert storage.get_schema("test_schema") is None

    # Delete non-existent schema
    assert storage.delete_schema("nonexistent") is False


def test_schema_activation(temp_storage_dir, test_schema):
    """Test schema activation functionality."""
    storage = SchemaStorage(temp_storage_dir)

    # Store v1 (active)
    storage.store_schema(test_schema, make_active=True)

    # Store v2 (inactive)
    v2_schema = Schema(
        name="test_schema",
        version=SchemaVersion(major=1, minor=1, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields=test_schema.fields.copy(),
        required_fields=test_schema.required_fields.copy(),
        description="Test schema v2",
    )
    storage.store_schema(v2_schema, make_active=False)

    # Verify active version
    active = storage.get_schema("test_schema")
    assert active is not None
    assert active.version.minor == 0  # v1 is active

    # Make v2 active
    storage.store_schema(v2_schema, make_active=True)
    active = storage.get_schema("test_schema")
    assert active is not None
    assert active.version.minor == 1  # v2 is now active
