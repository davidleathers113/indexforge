"""Schema management package for document index structures.

This package provides tools for defining, validating, and migrating document
schemas in the vector index. It ensures data consistency and proper structure
through schema validation and handles schema evolution through migrations.

Classes:
    SchemaDefinition: Class for defining document schemas and their properties
    SchemaValidator: Class for validating documents against defined schemas
    SchemaMigrator: Class for handling schema migrations and updates

Example:
    ```python
    from src.indexing.schema import SchemaDefinition, SchemaValidator, SchemaMigrator

    # Define a document schema
    schema = SchemaDefinition(
        name="Document",
        properties={
            "content": {"type": "text"},
            "embedding": {"type": "vector", "dimension": 768},
            "metadata": {"type": "object"}
        }
    )

    # Validate a document against the schema
    validator = SchemaValidator(schema)
    doc = {
        "content": "Document text",
        "embedding": [...],  # 768-dimensional vector
        "metadata": {"source": "notion"}
    }
    is_valid = validator.validate(doc)

    # Handle schema migration
    migrator = SchemaMigrator(schema)
    migrator.add_property("timestamp", {"type": "datetime"})
    migrator.migrate()
    ```

Note:
    Schema changes should be handled carefully as they may require reindexing
    or data migration in production environments.
"""

from .schema_definition import SchemaDefinition
from .schema_migrator import SchemaMigrator
from .schema_validator import SchemaValidator
from .validators import validate_document_fields, validate_embedding


__all__ = [
    "SchemaDefinition",
    "SchemaMigrator",
    "SchemaValidator",
    "validate_document_fields",
    "validate_embedding",
]
