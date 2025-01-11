"""
Validation utilities for Weaviate schema definitions.

This module provides validation functions for schema components including:
- Class name validation against Weaviate naming rules
- Property validation for required fields and data types
- Configuration validation for vectorizer, index, and other settings

Example:
    ```python
    from src.indexing.schema.validators import validate_class_name

    # Validate a class name
    validate_class_name("Document")  # Valid
    validate_class_name("123")  # Raises ClassNameError
    ```
"""

import re
from typing import Dict, List

from src.indexing.schema.exceptions import (
    ClassNameError,
    ConfigurationError,
    PropertyValidationError,
    SchemaValidationError,
)

# Regex pattern for valid class names
CLASS_NAME_PATTERN = r"^[A-Z][a-zA-Z0-9]*$"


def validate_class_name(class_name: str) -> None:
    """
    Validate a class name against Weaviate naming rules.

    Args:
        class_name (str): Name to validate

    Raises:
        ClassNameError: If the class name is invalid

    Example:
        ```python
        validate_class_name("Document")  # Valid
        validate_class_name("")  # Raises ClassNameError
        validate_class_name("123")  # Raises ClassNameError
        ```
    """
    if not class_name or not class_name.strip():
        raise ClassNameError(class_name, "Class name cannot be empty")

    if not re.match(CLASS_NAME_PATTERN, class_name):
        raise ClassNameError(
            class_name,
            "Class name must start with an uppercase letter and "
            "contain only letters and numbers",
        )


def validate_properties(properties: List[Dict]) -> None:
    """
    Validate schema properties.

    Args:
        properties (List[Dict]): List of property definitions

    Raises:
        PropertyValidationError: If any property is invalid
        SchemaValidationError: If the properties list is invalid

    Example:
        ```python
        properties = [
            {
                "name": "content",
                "dataType": ["text"],
                "description": "The document content",
            }
        ]
        validate_properties(properties)  # Valid
        validate_properties([{"name": "test"}])  # Raises PropertyValidationError
        ```
    """
    if not isinstance(properties, list):
        raise SchemaValidationError("Properties must be a list")

    property_names = set()
    for prop in properties:
        if not isinstance(prop, dict):
            raise PropertyValidationError(
                str(prop),
                "Property must be a dictionary",
            )

        name = prop.get("name")
        if not name:
            raise PropertyValidationError(
                str(prop),
                "Property must have a name",
            )

        if name in property_names:
            raise PropertyValidationError(
                name,
                "Duplicate property name",
            )

        property_names.add(name)

        if "dataType" not in prop:
            raise PropertyValidationError(
                name,
                "Property must have a dataType",
            )


def validate_configuration(config: Dict, config_name: str) -> None:
    """
    Validate a configuration section.

    Args:
        config (Dict): Configuration to validate
        config_name (str): Name of the configuration section

    Raises:
        ConfigurationError: If the configuration is invalid

    Example:
        ```python
        config = {
            "vectorizer": "text2vec-transformers",
            "moduleConfig": {
                "text2vec-transformers": {
                    "model": "sentence-transformers/all-mpnet-base-v2"
                }
            }
        }
        validate_configuration(config, "vectorizer")  # Valid
        validate_configuration({}, "vectorizer")  # Raises ConfigurationError
        ```
    """
    if not isinstance(config, dict):
        raise ConfigurationError(
            config_name,
            f"Configuration must be a dictionary, got {type(config)}",
        )

    required_keys = {
        "vectorizer": {"vectorizer", "moduleConfig"},
        "invertedIndexConfig": {"bm25"},
        "vectorIndexConfig": {"distance"},
    }

    if config_name in required_keys:
        missing = required_keys[config_name] - set(config.keys())
        if missing:
            raise ConfigurationError(
                config_name,
                f"Missing required keys: {', '.join(missing)}",
            )
