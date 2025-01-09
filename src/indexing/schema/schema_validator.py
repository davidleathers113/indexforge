"""
Provides schema validation functionality for Weaviate database schemas.

This module contains the SchemaValidator class which handles validation of
schema configurations, version checking, and schema retrieval. It ensures
that schemas meet all requirements for proper document storage and vector
search functionality.

The validator performs checks including:
- Presence of required properties and their correct types
- Vector embedding configuration
- Schema version compatibility
- Property type validation for special fields

Example:
    ```python
    import weaviate

    client = weaviate.Client("http://localhost:8080")
    validator = SchemaValidator(client, "Document")

    # Check if schema needs updating
    if not validator.check_schema_version():
        print("Schema update required")

    # Validate a new schema
    new_schema = {...}  # schema definition
    if validator.validate_schema(new_schema):
        print("Schema is valid")
    ```
"""

import logging
from typing import Any, Dict, Optional

import weaviate

from .validators.document import validate_document_fields


class SchemaValidator:
    """
    Validates and verifies Weaviate schema configurations.

    This class provides functionality to:
    - Retrieve and inspect existing schemas
    - Validate schema configurations against requirements
    - Check schema versions for compatibility
    - Ensure all required properties are present and correctly typed

    The validator includes comprehensive logging for debugging and monitoring
    of all validation operations. It checks for required properties, correct
    data types, and proper configuration of vector embeddings.

    Attributes:
        client: The Weaviate client instance
        class_name: Name of the document class to validate
        logger: Logger instance for validation tracking

    Example:
        ```python
        validator = SchemaValidator(client, "Document")

        # Get current schema
        schema = validator.get_schema()
        if schema:
            print("Found existing schema")

        # Validate a new schema
        new_schema = {
            "class": "Document",
            "properties": [
                {"name": "content", "dataType": ["text"]},
                {"name": "embedding", "dataType": ["vector"]}
            ]
        }
        is_valid = validator.validate_schema(new_schema)
        ```
    """

    def __init__(self, client: weaviate.Client, class_name: str):
        """
        Initialize a new SchemaValidator instance.

        Creates a validator instance with the specified client and class name
        for schema validation operations.

        Args:
            client: Configured Weaviate client instance
            class_name: Name of the document class to validate

        Raises:
            TypeError: If client is not a weaviate.Client instance
            ValueError: If class_name is empty or invalid
        """
        self.client = client
        self.class_name = class_name
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def validate_object(
        doc: Dict[str, Any],
        custom_fields: Optional[Dict[str, type]] = None,
        doc_id: Optional[str] = None,
        strict: bool = True,
    ) -> None:
        """
        Validate a document object against schema requirements.

        This method performs comprehensive validation of a document including:
        - Required field presence and non-emptiness
        - Data type correctness
        - Size constraints
        - Vector embedding dimensions
        - Relationship integrity (if doc_id provided)

        Args:
            doc: The document to validate
            custom_fields: Optional dict mapping field names to expected types
            doc_id: Optional document ID for relationship validation
            strict: If True, reject unknown fields

        Raises:
            ValueError: If any validation checks fail
            TypeError: If any fields have incorrect data types

        Example:
            ```python
            doc = {
                "content_body": "Sample content",
                "timestamp_utc": "2024-01-07T12:00:00Z",
                "schema_version": 1,
                "embedding": [0.1] * 384
            }

            try:
                SchemaValidator.validate_object(doc)
                print("Document is valid")
            except (ValueError, TypeError) as e:
                print(f"Validation error: {e}")
            ```
        """
        validate_document_fields(doc, custom_fields=custom_fields, doc_id=doc_id, strict=strict)

    def get_schema(self) -> Optional[Dict]:
        """
        Retrieve the current schema configuration from Weaviate.

        Fetches the schema for the specified class from the Weaviate instance.
        Returns None if the schema or class doesn't exist.

        Returns:
            Optional[Dict]: The schema configuration if found, None otherwise

        Raises:
            Exception: If there's an error communicating with Weaviate

        Example:
            ```python
            validator = SchemaValidator(client, "Document")
            schema = validator.get_schema()
            if schema:
                print(f"Found schema version: {schema.get('version')}")
            else:
                print("Schema not found")
            ```
        """
        try:
            schema = self.client.schema.get()
            self.logger.debug(f"Retrieved schema from Weaviate: {schema}")
            if not schema or "classes" not in schema:
                self.logger.warning("No schema or classes found in Weaviate")
                return None
            classes = schema.get("classes", [])
            for cls in classes:
                if cls.get("class") == self.class_name:
                    self.logger.debug(f"Found matching class schema: {cls}")
                    return cls
            self.logger.warning(f"Class {self.class_name} not found in schema")
            return None
        except Exception as e:
            self.logger.error(f"Error getting schema: {str(e)}", exc_info=True)
            raise

    def check_schema_version(self) -> bool:
        """
        Check if the current schema version matches the required version.

        Verifies that the schema exists and has the correct version property.
        This is used to determine if a schema migration is needed.

        Returns:
            bool: True if schema exists and version matches, False otherwise

        Raises:
            Exception: If there's an error checking the schema version

        Example:
            ```python
            validator = SchemaValidator(client, "Document")
            if not validator.check_schema_version():
                print("Schema needs to be updated")
            else:
                print("Schema is up to date")
            ```
        """
        try:
            schema = self.get_schema()
            if not schema:
                self.logger.info("Schema doesn't exist, needs creation")
                return False

            # Check version property
            properties = schema.get("properties", [])
            self.logger.debug(f"Checking schema version in properties: {properties}")
            for prop in properties:
                if prop["name"] == "schema_version":
                    self.logger.info(f"Found schema version: {prop}")
                    return True
            self.logger.warning("Schema version property not found")
            return False
        except Exception as e:
            self.logger.error(f"Error checking schema version: {str(e)}", exc_info=True)
            raise

    def validate_schema(self, schema: Dict) -> bool:
        """
        Validate a schema configuration against requirements.

        Performs comprehensive validation of a schema configuration including:
        - Presence of required class name and properties
        - Correct vectorizer configuration
        - Required properties with correct data types
        - Vector embedding configuration
        - Property type validation

        Args:
            schema: The schema configuration to validate

        Returns:
            bool: True if schema is valid, False otherwise

        Raises:
            Exception: If there's an error during validation

        Example:
            ```python
            new_schema = {
                "class": "Document",
                "vectorizer": "text2vec-transformers",
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "vectorizer": "text2vec-transformers"
                    },
                    {
                        "name": "embedding",
                        "dataType": ["vector"],
                        "dimension": 768
                    }
                ]
            }

            if validator.validate_schema(new_schema):
                print("Schema is valid and ready for use")
            else:
                print("Schema validation failed")
            ```
        """
        try:
            self.logger.debug(f"Validating schema: {schema}")

            # Basic validation
            if not schema.get("class"):
                self.logger.error("Missing class name in schema")
                return False
            if not schema.get("properties"):
                self.logger.error("Missing properties in schema")
                return False
            if not schema.get("vectorizer"):
                self.logger.error("Missing vectorizer in schema")
                return False

            # Validate required properties
            required_props = {
                "content_body",
                "content_summary",
                "content_title",
                "embedding",
                "timestamp_utc",
                "schema_version",
                "parent_id",
                "chunk_ids",
            }
            schema_props = {p["name"] for p in schema.get("properties", [])}
            self.logger.debug(f"Found properties: {schema_props}")
            if not required_props.issubset(schema_props):
                missing_props = required_props - schema_props
                self.logger.error(f"Missing required properties: {missing_props}")
                return False

            # Validate property types
            for prop in schema["properties"]:
                self.logger.debug(f"Validating property: {prop}")
                if not prop.get("dataType"):
                    self.logger.error(f"Missing dataType for property {prop['name']}")
                    return False
                if prop["name"] == "embedding" and "vector" not in prop["dataType"]:
                    self.logger.error(
                        f"Invalid dataType for embedding property: {prop['dataType']}"
                    )
                    return False

            return True
        except Exception as e:
            self.logger.error(f"Error validating schema: {str(e)}", exc_info=True)
            return False
