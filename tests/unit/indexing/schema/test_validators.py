"""Unit tests for schema validation utilities."""

import pytest

from src.indexing.schema.exceptions import (
    ClassNameError,
    ConfigurationError,
    PropertyValidationError,
    SchemaValidationError,
)
from src.indexing.schema.validators import (
    validate_class_name,
    validate_configuration,
    validate_properties,
)


def test_validate_class_name_valid():
    """Test that valid class names are accepted."""
    valid_names = ["Document", "MyClass", "Test123", "UserProfile"]
    for name in valid_names:
        validate_class_name(name)  # Should not raise


def test_validate_class_name_empty():
    """Test that empty class names are rejected."""
    with pytest.raises(ClassNameError) as exc_info:
        validate_class_name("")
    assert "empty" in str(exc_info.value)

    with pytest.raises(ClassNameError) as exc_info:
        validate_class_name("   ")
    assert "empty" in str(exc_info.value)


def test_validate_class_name_invalid_format():
    """Test that invalid class name formats are rejected."""
    invalid_names = ["123Test", "test", "Test-Class", "Test_Class", "TEST"]
    for name in invalid_names:
        with pytest.raises(ClassNameError) as exc_info:
            validate_class_name(name)
        assert "uppercase letter" in str(exc_info.value)


def test_validate_properties_valid():
    """Test that valid properties are accepted."""
    valid_properties = [
        {
            "name": "content",
            "dataType": ["text"],
            "description": "The document content",
        },
        {
            "name": "embedding",
            "dataType": ["vector"],
            "moduleConfig": {"vectorizer": "text2vec-transformers"},
        },
    ]
    validate_properties(valid_properties)  # Should not raise


def test_validate_properties_invalid_type():
    """Test that non-list properties are rejected."""
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_properties(None)
    assert "must be a list" in str(exc_info.value)

    with pytest.raises(SchemaValidationError) as exc_info:
        validate_properties({"name": "test"})
    assert "must be a list" in str(exc_info.value)


def test_validate_properties_invalid_property():
    """Test that invalid property definitions are rejected."""
    with pytest.raises(PropertyValidationError) as exc_info:
        validate_properties([None])
    assert "must be a dictionary" in str(exc_info.value)

    with pytest.raises(PropertyValidationError) as exc_info:
        validate_properties([{"dataType": ["text"]}])
    assert "must have a name" in str(exc_info.value)

    with pytest.raises(PropertyValidationError) as exc_info:
        validate_properties([{"name": "test"}])
    assert "must have a dataType" in str(exc_info.value)


def test_validate_properties_duplicate_names():
    """Test that duplicate property names are rejected."""
    properties = [
        {"name": "test", "dataType": ["text"]},
        {"name": "test", "dataType": ["text"]},
    ]
    with pytest.raises(PropertyValidationError) as exc_info:
        validate_properties(properties)
    assert "Duplicate" in str(exc_info.value)


def test_validate_configuration_valid():
    """Test that valid configurations are accepted."""
    vectorizer_config = {
        "vectorizer": "text2vec-transformers",
        "moduleConfig": {
            "text2vec-transformers": {
                "model": "sentence-transformers/all-mpnet-base-v2",
            }
        },
    }
    validate_configuration(vectorizer_config, "vectorizer")  # Should not raise

    inverted_index_config = {
        "bm25": {
            "b": 0.75,
            "k1": 1.2,
        }
    }
    validate_configuration(inverted_index_config, "invertedIndexConfig")  # Should not raise

    vector_index_config = {
        "distance": "cosine",
        "ef": 100,
        "maxConnections": 64,
    }
    validate_configuration(vector_index_config, "vectorIndexConfig")  # Should not raise


def test_validate_configuration_invalid_type():
    """Test that non-dict configurations are rejected."""
    with pytest.raises(ConfigurationError) as exc_info:
        validate_configuration(None, "vectorizer")
    assert "must be a dictionary" in str(exc_info.value)

    with pytest.raises(ConfigurationError) as exc_info:
        validate_configuration([], "vectorizer")
    assert "must be a dictionary" in str(exc_info.value)


def test_validate_configuration_missing_keys():
    """Test that configurations with missing required keys are rejected."""
    with pytest.raises(ConfigurationError) as exc_info:
        validate_configuration({"vectorizer": "text2vec-transformers"}, "vectorizer")
    assert "Missing required keys" in str(exc_info.value)
    assert "moduleConfig" in str(exc_info.value)

    with pytest.raises(ConfigurationError) as exc_info:
        validate_configuration({}, "invertedIndexConfig")
    assert "Missing required keys" in str(exc_info.value)
    assert "bm25" in str(exc_info.value)

    with pytest.raises(ConfigurationError) as exc_info:
        validate_configuration({}, "vectorIndexConfig")
    assert "Missing required keys" in str(exc_info.value)
    assert "distance" in str(exc_info.value)
