"""Facade for schema management operations.

This module provides a facade for schema management operations, offering a
simplified interface for schema handling while maintaining backward
compatibility with existing code.

Features:
1. Schema Management:
   - Schema creation
   - Schema updates
   - Schema validation
   - Migration support

2. Backward Compatibility:
   - Legacy interface support
   - API consistency
   - Version handling
   - Migration utilities

3. Resource Management:
   - Connection handling
   - Schema caching
   - Resource cleanup
   - Error recovery

Usage:
    ```python
    import weaviate
    from src.indexing.schema_manager import SchemaManager

    # Initialize client
    client = weaviate.Client("http://localhost:8080")

    # Create schema manager
    schema_manager = SchemaManager(
        client=client,
        class_name="Document"
    )

    # Use schema manager
    schema_manager.validate_schema()
    ```

Note:
    - Implements facade pattern
    - Maintains compatibility
    - Handles schema migrations
    - Provides validation
"""

import weaviate

from .schema import SchemaMigrator


class SchemaManager(SchemaMigrator):
    """Backward-compatible facade for schema operations.

    This class provides a simplified interface for schema management while
    maintaining compatibility with existing code. It handles schema creation,
    validation, and migration operations.

    Attributes:
        client: Weaviate client instance
        class_name: Name of the document class
    """

    def __init__(self, client: weaviate.Client, class_name: str):
        """Initialize schema manager.

        Args:
            client: Weaviate client instance for schema operations
            class_name: Name of the document class in Weaviate

        Example:
            >>> client = weaviate.Client("http://localhost:8080")
            >>> schema_manager = SchemaManager(
            ...     client=client,
            ...     class_name="Document"
            ... )
        """
        super().__init__(client, class_name)
