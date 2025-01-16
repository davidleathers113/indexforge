"""
Configuration constants for Weaviate schema definition.

This module contains all the configuration constants used in the schema definition,
including vectorizer settings, index configurations, and default property settings.
"""

from typing import Final


# Schema versioning
CURRENT_SCHEMA_VERSION: Final[int] = 2

# Vectorizer configuration
VECTORIZER_CONFIG: Final[dict] = {
    "vectorizer": "text2vec-transformers",
    "moduleConfig": {
        "text2vec-transformers": {
            "vectorizeClassName": False,
            "model": "sentence-transformers-all-MiniLM-L6-v2",
            "poolingStrategy": "mean",
            "maxTokens": 512,
        }
    },
}

# BM25 configuration for text search
INVERTED_INDEX_CONFIG: Final[dict] = {
    "bm25": {"b": 0.75, "k1": 1.2},
    "cleanupIntervalSeconds": 60,
    "stopwords": {"preset": "en"},
}

# Vector index configuration
VECTOR_INDEX_CONFIG: Final[dict] = {
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
    "quantizer": {"enabled": True, "bits": 8, "type": "scalar"},
    "pq": {
        "enabled": True,
        "encoder": {"type": "kmeans", "distribution": "log-normal"},
        "segments": 0,
        "centroids": 256,
        "bits": 8,
    },
}

# Property-specific vector index configuration
PROPERTY_VECTOR_INDEX_CONFIG: Final[dict] = {
    "distance": "cosine",
    "ef": 100,
    "efConstruction": 128,
    "maxConnections": 64,
    "vectorCacheMaxObjects": 500000,
    "quantizer": {"enabled": True, "bits": 8, "type": "scalar"},
}

# Replication configuration
REPLICATION_CONFIG: Final[dict] = {"factor": 2}

# Multi-tenancy configuration
MULTI_TENANCY_CONFIG: Final[dict] = {"enabled": True}

# Sharding configuration
SHARDING_CONFIG: Final[dict] = {
    "virtualPerPhysical": 128,
    "desiredCount": 3,
    "actualCount": 3,
    "function": "murmur3",
    "key": "id",
    "strategy": "hash",
}

# Default property configurations
DEFAULT_TEXT_PROPERTY_CONFIG: Final[dict] = {
    "dataType": ["text"],
    "moduleConfig": {"text2vec-transformers": {"skip": True}},
    "indexFilterable": True,
    "indexSearchable": True,
}

DEFAULT_VECTOR_PROPERTY_CONFIG: Final[dict] = {
    "dataType": ["number[]"],
    "moduleConfig": {"text2vec-transformers": {"skip": True}},
    "vectorIndexType": "hnsw",
}

# Schema property definitions
SCHEMA_VERSION_PROPERTY: Final[dict] = {
    "name": "schema_version",
    "dataType": ["int"],
    "description": "Schema version number",
}

CONTENT_BODY_PROPERTY: Final[dict] = {
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
    "indexFilterable": True,
    "indexSearchable": True,
}

CONTENT_SUMMARY_PROPERTY: Final[dict] = {
    "name": "content_summary",
    **DEFAULT_TEXT_PROPERTY_CONFIG,
    "description": "Document summary",
}

CONTENT_TITLE_PROPERTY: Final[dict] = {
    "name": "content_title",
    **DEFAULT_TEXT_PROPERTY_CONFIG,
    "description": "Document title",
}

EMBEDDING_PROPERTY: Final[dict] = {
    "name": "embedding",
    **DEFAULT_VECTOR_PROPERTY_CONFIG,
    "description": "Content embedding vector",
    "vectorIndexConfig": PROPERTY_VECTOR_INDEX_CONFIG,
}

TIMESTAMP_PROPERTY: Final[dict] = {
    "name": "timestamp_utc",
    "dataType": ["date"],
    "description": "Document timestamp in UTC",
    "indexFilterable": True,
}

PARENT_ID_PROPERTY: Final[dict] = {
    "name": "parent_id",
    "dataType": ["text"],
    "description": "Parent document reference",
    "indexFilterable": True,
}

CHUNK_IDS_PROPERTY: Final[dict] = {
    "name": "chunk_ids",
    "dataType": ["text[]"],
    "description": "Child chunk references",
    "indexFilterable": True,
}
