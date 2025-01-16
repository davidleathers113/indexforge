"""
Schema validation utilities for Weaviate.

This module provides a validator class for schema components, ensuring that
all parts of a schema meet Weaviate's requirements before creation.

Example:
    ```python
    from src.indexing.schema.validator import SchemaValidator

    # Validate a schema class name
    SchemaValidator.validate_class_name("Document")

    # Validate schema properties
    SchemaValidator.validate_properties([
        {"name": "content", "dataType": ["text"]},
    ])

    # Validate configurations
    SchemaValidator.validate_configurations({
        "vectorizer": vectorizer_config,
        "invertedIndexConfig": inverted_index_config,
    })
    ```
"""

import re
from typing import Any

from src.indexing.schema.exceptions import (
    ClassNameError,
    ConfigurationError,
    PropertyValidationError,
    SchemaValidationError,
)


class SchemaValidator:
    """
    Validator for Weaviate schema components.

    This class provides static methods for validating various aspects of
    a Weaviate schema, including class names, properties, and configurations.
    Each method performs specific validation checks and raises appropriate
    exceptions if validation fails.

    Example:
        ```python
        # Validate a class name
        SchemaValidator.validate_class_name("Document")

        # Validate properties
        SchemaValidator.validate_properties([
            {
                "name": "content",
                "dataType": ["text"],
                "description": "Document content",
            }
        ])

        # Validate configurations
        SchemaValidator.validate_configurations({
            "vectorizer": {
                "vectorizer": "text2vec-transformers",
                "moduleConfig": {...}
            }
        })
        ```
    """

    CLASS_NAME_PATTERN = r"^[A-Z][a-zA-Z0-9]*$"

    @classmethod
    def validate_class_name(cls, class_name: str) -> None:
        """
        Validate a class name against Weaviate naming rules.

        Args:
            class_name (str): Name to validate

        Raises:
            ClassNameError: If the class name is invalid

        Example:
            ```python
            SchemaValidator.validate_class_name("Document")  # Valid
            SchemaValidator.validate_class_name("")  # Raises ClassNameError
            SchemaValidator.validate_class_name("123")  # Raises ClassNameError
            ```
        """
        if not class_name or not class_name.strip():
            raise ClassNameError(class_name, "Class name cannot be empty")

        if not re.match(cls.CLASS_NAME_PATTERN, class_name):
            raise ClassNameError(
                class_name,
                "Class name must start with an uppercase letter and "
                "contain only letters and numbers",
            )

    @staticmethod
    def validate_properties(properties: list[dict[str, Any]]) -> None:
        """
        Validate schema properties.

        Args:
            properties (List[Dict[str, Any]]): List of property definitions

        Raises:
            PropertyValidationError: If any property is invalid
            SchemaValidationError: If the properties list is invalid

        Example:
            ```python
            SchemaValidator.validate_properties([
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Document content",
                }
            ])  # Valid
            SchemaValidator.validate_properties([
                {"name": "test"}
            ])  # Raises PropertyValidationError
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

    @staticmethod
    def validate_configurations(configs: dict[str, dict[str, Any]]) -> None:
        """
        Validate schema configurations.

        Args:
            configs (Dict[str, Dict[str, Any]]): Dictionary of configuration sections

        Raises:
            ConfigurationError: If any configuration is invalid

        Example:
            ```python
            SchemaValidator.validate_configurations({
                "vectorizer": {
                    "vectorizer": "text2vec-transformers",
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "model": "sentence-transformers/all-mpnet-base-v2"
                        }
                    }
                },
                "invertedIndexConfig": {
                    "bm25": {"b": 0.75, "k1": 1.2}
                }
            })  # Valid
            ```
        """
        required_keys = {
            "vectorizer": {"vectorizer", "moduleConfig"},
            "invertedIndexConfig": {"bm25"},
            "vectorIndexConfig": {"distance"},
        }

        for config_name, config in configs.items():
            if not isinstance(config, dict):
                raise ConfigurationError(
                    config_name,
                    f"Configuration must be a dictionary, got {type(config)}",
                )

            if config_name in required_keys:
                missing = required_keys[config_name] - set(config.keys())
                if missing:
                    raise ConfigurationError(
                        config_name,
                        f"Missing required keys: {', '.join(missing)}",
                    )
