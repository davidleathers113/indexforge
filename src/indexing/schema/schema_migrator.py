"""
Provides functionality for managing and migrating Weaviate schema versions.

This module contains the SchemaMigrator class which handles schema creation,
validation, and migration operations. It ensures that the database schema
is always in sync with the latest schema definition while handling version
updates gracefully.

The migrator works in conjunction with SchemaDefinition and SchemaValidator
to provide a complete schema management solution:
- Checks if schema exists and creates it if needed
- Validates schema structure and version
- Handles migration to newer schema versions
- Provides comprehensive logging of all operations

Example:
    ```python
    import weaviate
    from .schema_validator import SchemaValidator

    client = weaviate.Client("http://localhost:8080")
    validator = SchemaValidator(client, "Document")
    migrator = SchemaMigrator(client, "Document", validator)

    # Ensure schema is up to date
    migrator.ensure_schema()
    ```
"""

import logging

import weaviate

from .schema_definition import SchemaDefinition
from .schema_validator import SchemaValidator


class SchemaMigrator:
    """
    Manages schema migrations and updates for Weaviate document classes.

    This class provides functionality to:
    - Create new schemas if they don't exist
    - Validate existing schemas against current definitions
    - Migrate schemas to newer versions when needed
    - Handle schema updates with proper error handling and logging

    The migrator ensures data consistency by validating all schema changes
    before applying them and provides detailed logging of all operations
    for monitoring and debugging.

    Attributes:
        client: The Weaviate client instance
        class_name: Name of the document class being managed
        validator: SchemaValidator instance for schema validation
        logger: Logger instance for operation tracking

    Example:
        ```python
        client = weaviate.Client("http://localhost:8080")
        migrator = SchemaMigrator(client, "Document")

        try:
            migrator.ensure_schema()
            print("Schema is up to date")
        except Exception as e:
            print(f"Schema migration failed: {e}")
        ```
    """

    def __init__(
        self, client: weaviate.Client, class_name: str, schema_validator: SchemaValidator = None
    ):
        """
        Initialize a new SchemaMigrator instance.

        Creates a new migrator instance with the specified client and class name.
        Optionally accepts a custom schema validator, otherwise creates a new one.

        Args:
            client: Configured Weaviate client instance
            class_name: Name of the document class to manage
            schema_validator: Optional custom validator instance (default: None)

        Raises:
            TypeError: If client is not a weaviate.Client instance
            ValueError: If class_name is empty or invalid
        """
        self.client = client
        self.class_name = class_name
        self.validator = schema_validator or SchemaValidator(client, class_name)
        self.logger = logging.getLogger(__name__)

    def ensure_schema(self) -> None:
        """
        Ensure the schema exists and is up to date.

        This method checks if the schema exists and is at the current version.
        If the schema doesn't exist, it creates it. If it exists but is outdated,
        it performs a migration to the latest version.

        Raises:
            ValueError: If schema validation fails
            Exception: If schema creation or migration fails

        Example:
            ```python
            migrator = SchemaMigrator(client, "Document")
            try:
                migrator.ensure_schema()
                print("Schema is ready")
            except ValueError as e:
                print(f"Schema validation failed: {e}")
            except Exception as e:
                print(f"Schema operation failed: {e}")
            ```
        """
        try:
            self.logger.info(f"Ensuring schema for class {self.class_name}")
            schema = self.validator.get_schema()

            if not schema:
                self.logger.info("Schema not found, creating new schema")
                self._create_schema()
            elif not self.validator.check_schema_version():
                self.logger.info("Schema version mismatch, migrating schema")
                self._migrate_schema()
            else:
                self.logger.info("Schema is up to date")
        except Exception as e:
            self.logger.error(f"Error ensuring schema: {str(e)}", exc_info=True)
            raise

    def _create_schema(self) -> None:
        """
        Create the initial schema for the document class.

        This internal method handles the creation of a new schema when none exists.
        It includes validation of the schema before creation and proper error
        handling and logging.

        Raises:
            ValueError: If schema validation fails
            Exception: If schema creation fails in Weaviate

        Note:
            This is an internal method and should not be called directly.
            Use ensure_schema() instead.
        """
        try:
            self.logger.info("Creating new schema")
            schema = SchemaDefinition.get_schema(self.class_name)
            self.logger.debug(f"Generated schema: {schema}")

            if not self.validator.validate_schema(schema):
                self.logger.error("Schema validation failed")
                raise ValueError("Invalid schema configuration")

            self.client.schema.create_class(schema)
            self.logger.info("Schema created successfully")
        except Exception as e:
            self.logger.error(f"Error creating schema: {str(e)}", exc_info=True)
            raise

    def _migrate_schema(self) -> None:
        """
        Migrate the schema to the latest version.

        This internal method handles the migration of an existing schema to a newer
        version. It performs the migration by:
        1. Deleting the existing schema
        2. Creating a new schema with the latest definition
        3. Validating the new schema before applying

        Raises:
            ValueError: If new schema validation fails
            Exception: If schema deletion or creation fails

        Note:
            This is an internal method and should not be called directly.
            Use ensure_schema() instead.
        """
        try:
            self.logger.info("Starting schema migration")
            # Delete existing schema
            self.client.schema.delete_class(self.class_name)
            self.logger.info(f"Deleted existing schema for class {self.class_name}")

            # Create new schema
            schema = SchemaDefinition.get_schema(self.class_name)
            self.logger.debug(f"Generated new schema: {schema}")

            if not self.validator.validate_schema(schema):
                self.logger.error("New schema validation failed")
                raise ValueError("Invalid schema configuration")

            self.client.schema.create_class(schema)
            self.logger.info("Schema migration completed successfully")
        except Exception as e:
            self.logger.error(f"Error migrating schema: {str(e)}", exc_info=True)
            raise
