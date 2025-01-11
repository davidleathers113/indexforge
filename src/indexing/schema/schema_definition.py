"""
Defines the schema structure for the Weaviate vector database.

This module provides the SchemaDefinition class which defines the complete schema
for document storage in Weaviate, including vector embeddings, content fields,
metadata, and relationships. The schema is designed to support efficient vector
search and text indexing.

Key features of the schema:
- Vector embeddings using text2vec-transformers
- BM25 text indexing with customized parameters
- HNSW vector index configuration for fast similarity search
- Support for document relationships (parent-child)
- Versioned schema design
- Quantization support for efficient storage
- Compound indexes for optimized queries
- Materialized views for aggregations

Example:
    ```python
    import weaviate
    from weaviate.collections import Collection

    client = weaviate.Client("http://localhost:8080")
    schema = SchemaDefinition.get_schema("Document")
    collection = Collection.create(client, schema)
    ```
"""

from typing import Dict, List

from src.indexing.schema.configurations import (
    CHUNK_IDS_PROPERTY,
    CONTENT_BODY_PROPERTY,
    CONTENT_SUMMARY_PROPERTY,
    CONTENT_TITLE_PROPERTY,
    CURRENT_SCHEMA_VERSION,
    EMBEDDING_PROPERTY,
    INVERTED_INDEX_CONFIG,
    MULTI_TENANCY_CONFIG,
    PARENT_ID_PROPERTY,
    REPLICATION_CONFIG,
    SCHEMA_VERSION_PROPERTY,
    SHARDING_CONFIG,
    TIMESTAMP_PROPERTY,
    VECTOR_INDEX_CONFIG,
    VECTORIZER_CONFIG,
)
from src.indexing.schema.validators import (
    validate_class_name,
    validate_configuration,
    validate_properties,
)


class SchemaDefinition:
    """
    Defines the complete schema structure for document storage in Weaviate.

    This class provides the schema definition that includes:
    - Vector embedding configuration using text2vec-transformers
    - Content fields (body, title, summary) with selective vectorization
    - Metadata fields (timestamp, version)
    - Relationship fields (parent_id, chunk_ids)
    - HNSW vector index configuration for similarity search
    - BM25 text index configuration for hybrid search
    - Quantization settings for efficient storage
    - Compound indexes for optimized queries

    The schema is versioned to support future updates while maintaining
    backward compatibility with existing documents.

    Attributes:
        SCHEMA_VERSION (int): Current version of the schema structure

    Example:
        ```python
        schema = SchemaDefinition.get_schema("Document")
        print(f"Schema version: {SchemaDefinition.SCHEMA_VERSION}")
        print(f"Collection name: {schema['class']}")
        print(f"Properties: {len(schema['properties'])}")
        ```
    """

    SCHEMA_VERSION = CURRENT_SCHEMA_VERSION

    @staticmethod
    def get_properties() -> List[Dict]:
        """
        Get the list of schema properties.

        Returns:
            List[Dict]: List of property definitions

        Example:
            ```python
            properties = SchemaDefinition.get_properties()
            for prop in properties:
                print(f"Property: {prop['name']}, Type: {prop['dataType']}")
            ```
        """
        return [
            SCHEMA_VERSION_PROPERTY,
            CONTENT_BODY_PROPERTY,
            CONTENT_SUMMARY_PROPERTY,
            CONTENT_TITLE_PROPERTY,
            EMBEDDING_PROPERTY,
            TIMESTAMP_PROPERTY,
            PARENT_ID_PROPERTY,
            CHUNK_IDS_PROPERTY,
        ]

    @staticmethod
    def get_configurations() -> Dict:
        """
        Get the schema configurations.

        Returns:
            Dict: Dictionary of configuration sections

        Example:
            ```python
            configs = SchemaDefinition.get_configurations()
            print(f"Vectorizer: {configs['vectorizer']}")
            print(f"Vector Index: {configs['vectorIndexConfig']}")
            ```
        """
        return {
            **VECTORIZER_CONFIG,
            "invertedIndexConfig": INVERTED_INDEX_CONFIG,
            "vectorIndexConfig": VECTOR_INDEX_CONFIG,
            "replicationConfig": REPLICATION_CONFIG,
            "multiTenancyConfig": MULTI_TENANCY_CONFIG,
            "shardingConfig": SHARDING_CONFIG,
        }

    @classmethod
    def get_schema(cls, class_name: str) -> Dict:
        """
        Get the complete schema definition for a given class name.

        Args:
            class_name (str): Name of the class/collection to create

        Returns:
            Dict: Complete schema definition including all configurations

        Raises:
            ClassNameError: If the class name is invalid
            PropertyValidationError: If any property is invalid
            ConfigurationError: If any configuration is invalid
            SchemaValidationError: If the overall schema is invalid

        Example:
            ```python
            schema = SchemaDefinition.get_schema("Document")
            collection = Collection.create(client, schema)
            ```
        """
        validate_class_name(class_name)

        properties = cls.get_properties()
        validate_properties(properties)

        configurations = cls.get_configurations()
        validate_configuration(configurations, "vectorizer")
        validate_configuration(configurations["invertedIndexConfig"], "invertedIndexConfig")
        validate_configuration(configurations["vectorIndexConfig"], "vectorIndexConfig")

        return {
            "class": class_name,
            "description": "A document with vector embeddings",
            **configurations,
            "properties": properties,
        }
