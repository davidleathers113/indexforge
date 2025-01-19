"""Unit tests for schema registry implementation."""

from pathlib import Path

import pytest

from src.core.schema.base import SchemaType, SchemaVersion
from src.core.schema.registry import (
    CacheConfig,
    CircularDependencyError,
    SchemaRegistry,
    SchemaRegistryError,
)
from src.core.schema.schema import FieldDefinition, Schema
from src.core.schema.storage import SchemaStorage


@pytest.fixture
def temp_storage_dir(tmp_path) -> Path:
    """Create temporary storage directory."""
    storage_dir = tmp_path / "schemas"
    storage_dir.mkdir()
    return storage_dir


@pytest.fixture
def storage(temp_storage_dir) -> SchemaStorage:
    """Create schema storage instance."""
    return SchemaStorage(temp_storage_dir)


@pytest.fixture
def cache_config() -> CacheConfig:
    """Create cache configuration."""
    return CacheConfig(ttl=60, max_size=10)


@pytest.fixture
def registry(storage: SchemaStorage, cache_config: CacheConfig) -> SchemaRegistry:
    """Create schema registry instance."""
    return SchemaRegistry(storage=storage, cache_config=cache_config)


@pytest.fixture
def test_schema() -> Schema:
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


@pytest.mark.asyncio
async def test_register_schema(registry: SchemaRegistry, test_schema: Schema):
    """Test registering a schema."""
    await registry.register_schema(test_schema)

    # Verify schema is stored
    retrieved = await registry.get_schema("test_schema")
    assert retrieved is not None
    assert retrieved.name == test_schema.name
    assert retrieved.version == test_schema.version
    assert retrieved.fields["title"].type == "string"


@pytest.mark.asyncio
async def test_schema_versioning(registry: SchemaRegistry, test_schema: Schema):
    """Test schema versioning functionality."""
    # Register v1
    await registry.register_schema(test_schema)

    # Create and register v2
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
    await registry.register_schema(v2_schema)

    # Get specific version
    v1 = await registry.get_schema("test_schema", SchemaVersion(major=1, minor=0, patch=0))
    assert v1 is not None
    assert len(v1.fields) == 2

    # Get active version (should be v2)
    active = await registry.get_schema("test_schema")
    assert active is not None
    assert active.version.minor == 1
    assert len(active.fields) == 3


@pytest.mark.asyncio
async def test_schema_caching(registry: SchemaRegistry, test_schema: Schema):
    """Test schema caching functionality."""
    await registry.register_schema(test_schema)

    # First retrieval should cache
    schema1 = await registry.get_schema("test_schema")
    assert schema1 is not None

    # Second retrieval should use cache
    schema2 = await registry.get_schema("test_schema")
    assert schema2 is not None
    assert schema2 is schema1  # Same instance due to caching

    # Invalidate cache
    await registry.invalidate_cache("test_schema")

    # Should retrieve from storage
    schema3 = await registry.get_schema("test_schema")
    assert schema3 is not None
    assert schema3 is not schema1  # Different instance after cache invalidation


@pytest.mark.asyncio
async def test_schema_listing(registry: SchemaRegistry, test_schema: Schema):
    """Test listing available schemas."""
    await registry.register_schema(test_schema)

    # Create and register chunk schema
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
    await registry.register_schema(chunk_schema)

    # List all schemas
    all_schemas = registry.list_schemas()
    assert len(all_schemas) == 2

    # List by type
    doc_schemas = registry.list_schemas(schema_type=SchemaType.DOCUMENT)
    assert len(doc_schemas) == 1
    assert doc_schemas[0].name == "test_schema"

    chunk_schemas = registry.list_schemas(schema_type=SchemaType.CHUNK)
    assert len(chunk_schemas) == 1
    assert chunk_schemas[0].name == "test_chunk"


@pytest.mark.asyncio
async def test_error_handling(registry: SchemaRegistry):
    """Test error handling in schema registry."""
    # Try to get non-existent schema
    schema = await registry.get_schema("nonexistent")
    assert schema is None

    # Try to get non-existent version
    schema = await registry.get_schema("nonexistent", SchemaVersion(major=1, minor=0, patch=0))
    assert schema is None

    # Try to register invalid schema
    with pytest.raises(SchemaRegistryError):
        await registry.register_schema(None)  # type: ignore


@pytest.mark.asyncio
async def test_schema_field_dependencies(registry: SchemaRegistry):
    """Test extraction of schema dependencies from fields."""
    # Create schemas with dependencies
    user_schema = Schema(
        name="user",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "name": FieldDefinition(type="string", required=True),
        },
        required_fields={"name"},
        description="User schema",
    )

    post_schema = Schema(
        name="post",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "title": FieldDefinition(type="string", required=True),
            "author": FieldDefinition(type="schema_ref", ref_schema="user"),
            "comments": FieldDefinition(type="array", items_schema="comment"),
        },
        required_fields={"title", "author"},
        description="Post schema",
    )

    # Register schemas
    await registry.register_schema(user_schema)
    await registry.register_schema(post_schema)

    # Verify dependencies
    deps = registry.get_dependencies("post")
    assert "user" in deps
    assert "comment" in deps


@pytest.mark.asyncio
async def test_schema_inheritance_dependencies(registry: SchemaRegistry):
    """Test extraction of schema dependencies from inheritance."""
    # Create base schema
    base_schema = Schema(
        name="base_doc",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "id": FieldDefinition(type="string", required=True),
            "created_at": FieldDefinition(type="datetime"),
        },
        required_fields={"id"},
        description="Base document schema",
    )

    # Create child schema
    child_schema = Schema(
        name="child_doc",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "title": FieldDefinition(type="string", required=True),
        },
        required_fields={"title"},
        parent_schema="base_doc",
        description="Child document schema",
    )

    # Register schemas
    await registry.register_schema(base_schema)
    await registry.register_schema(child_schema)

    # Verify dependencies
    deps = registry.get_dependencies("child_doc")
    assert "base_doc" in deps


@pytest.mark.asyncio
async def test_schema_validation_dependencies(registry: SchemaRegistry):
    """Test extraction of schema dependencies from validations."""
    # Create schemas with validation dependencies
    category_schema = Schema(
        name="category",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "name": FieldDefinition(type="string", required=True),
        },
        required_fields={"name"},
        description="Category schema",
    )

    product_schema = Schema(
        name="product",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "name": FieldDefinition(type="string", required=True),
            "category": FieldDefinition(type="string"),
        },
        required_fields={"name"},
        validation_schemas={"category"},
        description="Product schema",
    )

    # Register schemas
    await registry.register_schema(category_schema)
    await registry.register_schema(product_schema)

    # Verify dependencies
    deps = registry.get_dependencies("product")
    assert "category" in deps


@pytest.mark.asyncio
async def test_circular_dependency_detection(registry: SchemaRegistry):
    """Test detection of circular dependencies."""
    # Create schemas with circular dependency
    schema_a = Schema(
        name="schema_a",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "ref_b": FieldDefinition(type="schema_ref", ref_schema="schema_b"),
        },
        description="Schema A",
    )

    schema_b = Schema(
        name="schema_b",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "ref_c": FieldDefinition(type="schema_ref", ref_schema="schema_c"),
        },
        description="Schema B",
    )

    schema_c = Schema(
        name="schema_c",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "ref_a": FieldDefinition(type="schema_ref", ref_schema="schema_a"),
        },
        description="Schema C",
    )

    # Register schemas - should raise CircularDependencyError
    await registry.register_schema(schema_a)
    await registry.register_schema(schema_b)
    with pytest.raises(CircularDependencyError) as exc:
        await registry.register_schema(schema_c)
    assert "Circular dependency detected" in str(exc.value)


@pytest.mark.asyncio
async def test_missing_schema_reference(registry: SchemaRegistry):
    """Test handling of missing schema references."""
    # Create schema with missing reference
    invalid_schema = Schema(
        name="invalid",
        version=SchemaVersion(major=1, minor=0, patch=0),
        schema_type=SchemaType.DOCUMENT,
        fields={
            "ref": FieldDefinition(type="schema_ref"),  # Missing ref_schema
        },
        description="Invalid schema",
    )

    # Register schema - should raise SchemaRegistryError
    with pytest.raises(SchemaRegistryError) as exc:
        await registry.register_schema(invalid_schema)
    assert "Missing schema reference" in str(exc.value)
