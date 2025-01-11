"""
Unit tests for the schema definition module.

This module contains tests for the SchemaDefinition class and its methods,
ensuring proper schema generation and configuration.
"""

import pytest

from src.indexing.schema.configurations import (
    CURRENT_SCHEMA_VERSION,
    INVERTED_INDEX_CONFIG,
    SCHEMA_VERSION_PROPERTY,
    VECTOR_INDEX_CONFIG,
    VECTORIZER_CONFIG,
)
from src.indexing.schema.exceptions import (
    ClassNameError,
    ConfigurationError,
    PropertyValidationError,
    SchemaValidationError,
)
from src.indexing.schema.schema_definition import SchemaDefinition


def test_schema_version():
    """Test that the schema version matches the current version."""
    assert SchemaDefinition.SCHEMA_VERSION == CURRENT_SCHEMA_VERSION


def test_get_schema_basic_structure():
    """Test that get_schema returns a dictionary with all required top-level keys."""
    schema = SchemaDefinition.get_schema("TestClass")

    assert isinstance(schema, dict)
    assert schema["class"] == "TestClass"
    assert "description" in schema
    assert "properties" in schema
    assert "vectorIndexConfig" in schema
    assert "invertedIndexConfig" in schema


def test_get_schema_vectorizer_config():
    """Test that the schema includes correct vectorizer configuration."""
    schema = SchemaDefinition.get_schema("TestClass")

    assert schema["vectorizer"] == VECTORIZER_CONFIG["vectorizer"]
    assert schema["moduleConfig"] == VECTORIZER_CONFIG["moduleConfig"]


def test_get_schema_index_configs():
    """Test that the schema includes correct index configurations."""
    schema = SchemaDefinition.get_schema("TestClass")

    assert schema["invertedIndexConfig"] == INVERTED_INDEX_CONFIG
    assert schema["vectorIndexConfig"] == VECTOR_INDEX_CONFIG


def test_get_schema_properties():
    """Test that the schema includes all required properties."""
    schema = SchemaDefinition.get_schema("TestClass")
    properties = {prop["name"] for prop in schema["properties"]}

    required_properties = {
        "schema_version",
        "content_body",
        "content_summary",
        "content_title",
        "embedding",
        "timestamp_utc",
        "parent_id",
        "chunk_ids",
    }

    assert properties == required_properties


def test_schema_version_property():
    """Test that the schema version property is correctly configured."""
    schema = SchemaDefinition.get_schema("TestClass")
    version_prop = next(prop for prop in schema["properties"] if prop["name"] == "schema_version")

    assert version_prop == SCHEMA_VERSION_PROPERTY


def test_get_schema_with_different_class_names():
    """Test that get_schema works with different class names."""
    names = ["Test1", "Test2", "AnotherClass"]
    for name in names:
        schema = SchemaDefinition.get_schema(name)
        assert schema["class"] == name


def test_get_schema_immutability():
    """Test that subsequent calls to get_schema don't affect each other."""
    schema1 = SchemaDefinition.get_schema("Test1")
    schema2 = SchemaDefinition.get_schema("Test2")

    # Modify schema1
    schema1["properties"].append({"name": "new_prop", "dataType": ["text"]})

    # Check schema2 is unaffected
    schema2_props = {prop["name"] for prop in schema2["properties"]}
    assert "new_prop" not in schema2_props


@pytest.mark.parametrize(
    "invalid_name",
    [
        "",  # Empty string
        "   ",  # Whitespace
        "Invalid Name",  # Contains space
        "invalid-name",  # Contains hyphen
        "123invalid",  # Starts with number
    ],
)
def test_get_schema_with_invalid_class_names(invalid_name):
    """Test that get_schema validates class names."""
    with pytest.raises(ClassNameError) as exc_info:
        SchemaDefinition.get_schema(invalid_name)
    assert invalid_name in str(exc_info.value)


def test_validate_properties_with_invalid_list():
    """Test property validation with invalid list type."""
    with pytest.raises(SchemaValidationError) as exc_info:
        SchemaDefinition.validate_properties(None)
    assert "Properties must be a list" in str(exc_info.value)


def test_validate_properties_with_invalid_property():
    """Test property validation with invalid property type."""
    with pytest.raises(PropertyValidationError) as exc_info:
        SchemaDefinition.validate_properties([None])
    assert "Property must be a dictionary" in str(exc_info.value)


def test_validate_properties_with_missing_name():
    """Test property validation with missing name."""
    with pytest.raises(PropertyValidationError) as exc_info:
        SchemaDefinition.validate_properties([{"dataType": ["text"]}])
    assert "Property must have a name" in str(exc_info.value)


def test_validate_properties_with_duplicate_names():
    """Test property validation with duplicate names."""
    properties = [
        {"name": "test", "dataType": ["text"]},
        {"name": "test", "dataType": ["text"]},
    ]
    with pytest.raises(PropertyValidationError) as exc_info:
        SchemaDefinition.validate_properties(properties)
    assert "Duplicate property name" in str(exc_info.value)


def test_validate_properties_with_missing_data_type():
    """Test property validation with missing dataType."""
    with pytest.raises(PropertyValidationError) as exc_info:
        SchemaDefinition.validate_properties([{"name": "test"}])
    assert "Property must have a dataType" in str(exc_info.value)


def test_validate_configuration_with_invalid_type():
    """Test configuration validation with invalid type."""
    with pytest.raises(ConfigurationError) as exc_info:
        SchemaDefinition.validate_configuration(None, "test")
    assert "Configuration must be a dictionary" in str(exc_info.value)


def test_validate_configuration_with_missing_keys():
    """Test configuration validation with missing required keys."""
    with pytest.raises(ConfigurationError) as exc_info:
        SchemaDefinition.validate_configuration({}, "vectorizer")
    assert "Missing required keys" in str(exc_info.value)
    assert "vectorizer" in str(exc_info.value)
    assert "moduleConfig" in str(exc_info.value)
