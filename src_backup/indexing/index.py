"""Vector Index for handling indexing operations.

This module provides the core vector index functionality for document storage
and retrieval. It manages the connection to the vector database and handles
schema validation and operations.

Features:
1. Index Management:
   - Connection handling
   - Schema validation
   - Batch operations
   - Resource cleanup

2. Schema Validation:
   - Schema consistency checks
   - Type validation
   - Required field validation
   - Relationship validation

3. Operation Handling:
   - Document indexing
   - Document updates
   - Document deletion
   - Batch processing

Usage:
    ```python
    from src.indexing.index import VectorIndex
    from src.indexing.schema.schema_validator import SchemaValidator

    # Create vector index
    index = VectorIndex(
        client_url="http://localhost:8080",
        class_name="Document",
        batch_size=100
    )

    # Initialize with custom schema validator
    validator = SchemaValidator(client, "Document")
    index = VectorIndex(
        client_url="http://localhost:8080",
        class_name="Document",
        schema_validator=validator
    )
    ```

Note:
    - Manages database connections
    - Validates schema consistency
    - Handles batch operations
    - Provides error handling
"""

import weaviate

from .operations import Operations
from .schema.schema_validator import SchemaValidator


class VectorIndex:
    """Vector Index for handling indexing operations.

    This class provides core functionality for managing document storage and
    retrieval in a vector database. It handles connection management, schema
    validation, and operation execution.

    Attributes:
        client: Weaviate client instance
        class_name: Name of the document class
        batch_size: Size of batches for bulk operations
        schema_validator: Validator for schema consistency
        operations: Handler for index operations
    """

    def __init__(self, client_url, class_name, batch_size=100, *, schema_validator=None):
        """Initialize vector index.

        Args:
            client_url: URL of the Weaviate instance
            class_name: Name of the document class
            batch_size: Size of batches for bulk operations (default: 100)
            schema_validator: Optional schema validator instance

        Example:
            >>> index = VectorIndex(
            ...     client_url="http://localhost:8080",
            ...     class_name="Document",
            ...     batch_size=100
            ... )
        """
        self.client = weaviate.Client(client_url)
        self.class_name = class_name
        self.batch_size = batch_size
        self.schema_validator = schema_validator or SchemaValidator(self.client, self.class_name)
        self.operations = Operations(
            client=self.client,
            class_name=self.class_name,
            batch_size=self.batch_size,
            schema_validator=self.schema_validator,
        )
