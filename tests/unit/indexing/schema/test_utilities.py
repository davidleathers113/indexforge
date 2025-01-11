"""
Unit tests for the schema utilities module.

This module contains tests for the schema utility functions, ensuring proper
validation, comparison, and version management functionality.
"""

import pytest

from src.indexing.schema.configurations import CURRENT_SCHEMA_VERSION
from src.indexing.schema.utilities import (
    compare_schemas,
    get_schema_properties,
    get_schema_version,
    needs_migration,
    validate_schema_version,
)


@pytest.fixture
def valid_schema():
    """Fixture providing a valid schema for testing."""
    return {
        "class": "TestClass",
        "properties": [
            {
                "name": "schema_version",
                "dataType": ["int"],
                "description": "Schema version",
                "defaultValue": CURRENT_SCHEMA_VERSION,
            },
            {
                "name": "test_prop",
                "dataType": ["text"],
                "description": "Test property",
            },
        ],
    }


@pytest.fixture
def invalid_schema():
    """Fixture providing an invalid schema for testing."""
    return {
        "class": "TestClass",
        "properties": [
            {
                "name": "test_prop",
                "dataType": ["text"],
                "description": "Test property",
            },
        ],
    }


def test_validate_schema_version_with_valid_schema(valid_schema):
    """Test schema version validation with a valid schema."""
    assert validate_schema_version(valid_schema) is True


def test_validate_schema_version_with_invalid_schema(invalid_schema):
    """Test schema version validation with an invalid schema."""
    assert validate_schema_version(invalid_schema) is False


def test_validate_schema_version_with_wrong_type():
    """Test schema version validation with wrong version property type."""
    schema = {
        "properties": [
            {
                "name": "schema_version",
                "dataType": ["text"],  # Wrong type
                "description": "Schema version",
            }
        ]
    }
    assert validate_schema_version(schema) is False


def test_get_schema_properties_with_valid_schema(valid_schema):
    """Test property extraction from a valid schema."""
    properties = get_schema_properties(valid_schema)
    assert properties == {"schema_version", "test_prop"}


def test_get_schema_properties_with_invalid_schema():
    """Test property extraction from invalid schemas."""
    assert get_schema_properties({}) == set()
    assert get_schema_properties({"properties": None}) == set()
    assert get_schema_properties({"properties": []}) == set()


def test_compare_schemas_with_identical_schemas(valid_schema):
    """Test schema comparison with identical schemas."""
    differences = compare_schemas(valid_schema, valid_schema.copy())
    assert not differences


def test_compare_schemas_with_different_properties():
    """Test schema comparison with different properties."""
    schema1 = {
        "class": "Test",
        "properties": [{"name": "prop1"}],
    }
    schema2 = {
        "class": "Test",
        "properties": [{"name": "prop2"}],
    }

    differences = compare_schemas(schema1, schema2)
    assert len(differences) == 2
    assert any("Added properties: prop2" in diff for diff in differences)
    assert any("Removed properties: prop1" in diff for diff in differences)


def test_compare_schemas_with_different_attributes():
    """Test schema comparison with different basic attributes."""
    schema1 = {
        "class": "Test1",
        "vectorizer": "text2vec-1",
        "description": "desc1",
        "properties": [],
    }
    schema2 = {
        "class": "Test2",
        "vectorizer": "text2vec-2",
        "description": "desc2",
        "properties": [],
    }

    differences = compare_schemas(schema1, schema2)
    assert len(differences) == 3
    assert "Different class" in differences
    assert "Different vectorizer" in differences
    assert "Different description" in differences


def test_get_schema_version_with_valid_schema(valid_schema):
    """Test version extraction from a valid schema."""
    version = get_schema_version(valid_schema)
    assert version == CURRENT_SCHEMA_VERSION


def test_get_schema_version_with_invalid_schema(invalid_schema):
    """Test version extraction from an invalid schema."""
    version = get_schema_version(invalid_schema)
    assert version is None


def test_get_schema_version_with_invalid_version_value():
    """Test version extraction with invalid version value."""
    schema = {
        "properties": [
            {
                "name": "schema_version",
                "defaultValue": "invalid",
            }
        ]
    }
    version = get_schema_version(schema)
    assert version is None


def test_needs_migration_with_old_version():
    """Test migration check with old version."""
    schema = {
        "properties": [
            {
                "name": "schema_version",
                "defaultValue": CURRENT_SCHEMA_VERSION - 1,
            }
        ]
    }
    assert needs_migration(schema) is True


def test_needs_migration_with_current_version(valid_schema):
    """Test migration check with current version."""
    assert needs_migration(valid_schema) is False


def test_needs_migration_with_invalid_schema(invalid_schema):
    """Test migration check with invalid schema."""
    assert needs_migration(invalid_schema) is True
