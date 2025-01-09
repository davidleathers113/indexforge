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

Example:
    ```python
    import weaviate

    client = weaviate.Client("http://localhost:8080")
    schema = SchemaDefinition.get_schema("Document")
    client.schema.create_class(schema)
    ```
"""

from typing import Dict


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

    The schema is versioned to support future updates while maintaining
    backward compatibility with existing documents.

    Attributes:
        SCHEMA_VERSION (int): Current version of the schema structure

    Example:
        ```python
        schema = SchemaDefinition.get_schema("Document")
        print(f"Schema version: {SchemaDefinition.SCHEMA_VERSION}")
        print(f"Class name: {schema['class']}")
        print(f"Properties: {len(schema['properties'])}")
        ```
    """

    SCHEMA_VERSION = 1

    @classmethod
    def get_schema(cls, class_name: str) -> Dict:
        """
        Get the complete schema definition for a document class.

        This method returns a dictionary containing the full schema definition
        including all properties, vectorizer configuration, and index settings.
        The schema is optimized for both vector and text-based search.

        Args:
            class_name: Name to use for the document class in Weaviate

        Returns:
            Dict: Complete schema definition ready for Weaviate import with:
                - class: The specified class name
                - vectorizer: text2vec-transformers configuration
                - properties: List of all property definitions
                - vectorIndexConfig: HNSW index settings
                - invertedIndexConfig: BM25 settings

        Example:
            ```python
            schema = SchemaDefinition.get_schema("Document")

            # Access specific configurations
            vectorizer = schema["moduleConfig"]["text2vec-transformers"]
            vector_index = schema["vectorIndexConfig"]
            properties = schema["properties"]

            # Print key settings
            print(f"Model: {vectorizer['model']}")
            print(f"Distance metric: {vector_index['distance']}")
            print(f"Number of properties: {len(properties)}")
            ```
        """
        return {
            "class": class_name,
            "description": "A document with vector embeddings",
            "vectorizer": "text2vec-transformers",
            "moduleConfig": {
                "text2vec-transformers": {
                    "vectorizeClassName": False,
                    "model": "sentence-transformers-all-MiniLM-L6-v2",
                    "poolingStrategy": "mean",
                    "maxTokens": 512,
                }
            },
            "invertedIndexConfig": {
                "bm25": {"b": 0.75, "k1": 1.2},
                "cleanupIntervalSeconds": 60,
                "stopwords": {"preset": "en"},
            },
            "vectorIndexConfig": {
                "skip": False,
                "cleanupIntervalSeconds": 300,
                "maxConnections": 32,
                "efConstruction": 128,
                "ef": -1,
                "dynamicEfMin": 100,
                "dynamicEfMax": 500,
                "dynamicEfFactor": 8,
                "vectorCacheMaxObjects": 1000000,
                "flatSearchCutoff": 40000,
                "distance": "cosine",
            },
            "properties": [
                # Schema version property
                {
                    "name": "schema_version",
                    "dataType": ["int"],
                    "description": "Schema version number",
                },
                # Content properties
                {
                    "name": "content_body",
                    "dataType": ["text"],
                    "description": "Main document content",
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "skip": False,
                            "vectorizePropertyName": False,
                            "poolingStrategy": "mean",
                            "maxTokens": 512,
                        }
                    },
                },
                {
                    "name": "content_summary",
                    "dataType": ["text"],
                    "description": "Document summary",
                    "moduleConfig": {
                        "text2vec-transformers": {"skip": True, "vectorizePropertyName": False}
                    },
                },
                {
                    "name": "content_title",
                    "dataType": ["text"],
                    "description": "Document title",
                    "moduleConfig": {
                        "text2vec-transformers": {"skip": True, "vectorizePropertyName": False}
                    },
                },
                # Embedding properties
                {
                    "name": "embedding",
                    "dataType": ["number[]"],
                    "description": "Content embedding",
                    "moduleConfig": {"text2vec-transformers": {"skip": True}},
                    "vectorIndexType": "hnsw",
                    "vectorIndexConfig": {
                        "distance": "cosine",
                        "ef": 100,
                        "efConstruction": 128,
                        "maxConnections": 64,
                        "vectorCacheMaxObjects": 500000,
                    },
                },
                # Metadata properties
                {
                    "name": "timestamp_utc",
                    "dataType": ["date"],
                    "description": "Document timestamp",
                },
                # Relationship properties
                {
                    "name": "parent_id",
                    "dataType": ["string"],
                    "description": "Parent document ID",
                },
                {
                    "name": "chunk_ids",
                    "dataType": ["string[]"],
                    "description": "Child chunk IDs",
                },
            ],
        }
