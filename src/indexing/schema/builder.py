"""
Builder class for constructing Weaviate schemas.

This module provides the `SchemaBuilder` class, which offers a fluent
interface for schema construction.
"""

from typing import Any, Dict, List

from src.indexing.schema.configuration_builder import ConfigurationBuilder
from src.indexing.schema.configurations import (
    CURRENT_SCHEMA_VERSION,
    MULTI_TENANCY_CONFIG,
    REPLICATION_CONFIG,
    SHARDING_CONFIG,
)
from src.indexing.schema.validator import SchemaValidator


class SchemaBuilder:
    """
    Builder class for constructing Weaviate schemas.
    """

    def __init__(self, class_name: str) -> None:
        SchemaValidator.validate_class_name(class_name)
        self.class_name = class_name
        self.properties: List[Dict[str, Any]] = []
        self.vectorizer_config = ConfigurationBuilder.vectorizer_config("text2vec-transformers")
        self.inverted_index_config = ConfigurationBuilder.bm25_config()
        self.vector_index_config = ConfigurationBuilder.vector_index_config()
        self.replication_config = dict(REPLICATION_CONFIG)
        self.multi_tenancy_config = dict(MULTI_TENANCY_CONFIG)
        self.sharding_config = dict(SHARDING_CONFIG)

        # Add schema version property by default
        self.add_int_property(
            "schema_version",
            description="Schema version for compatibility",
            default_value=CURRENT_SCHEMA_VERSION,
        )

    def add_text_property(self, name: str, **kwargs: Any) -> "SchemaBuilder":
        property_def = self._create_property(name, "text", **kwargs)
        self.properties.append(property_def)
        return self

    def add_vector_property(self, name: str, **kwargs: Any) -> "SchemaBuilder":
        property_def = self._create_property(name, "vector", **kwargs)
        self.properties.append(property_def)
        return self

    def add_int_property(self, name: str, **kwargs: Any) -> "SchemaBuilder":
        property_def = self._create_property(name, "int", **kwargs)
        self.properties.append(property_def)
        return self

    def add_reference_property(
        self, name: str, target_class: str, **kwargs: Any
    ) -> "SchemaBuilder":
        property_def = self._create_property(name, "cross-reference", **kwargs)
        property_def["crossReference"] = {"target": [target_class]}
        self.properties.append(property_def)
        return self

    def with_vectorizer(self, vectorizer: str, **kwargs: Any) -> "SchemaBuilder":
        self.vectorizer_config = ConfigurationBuilder.vectorizer_config(vectorizer, **kwargs)
        return self

    def with_vector_index(self, **kwargs: Any) -> "SchemaBuilder":
        self.vector_index_config = ConfigurationBuilder.vector_index_config(**kwargs)
        return self

    def with_bm25(self, **kwargs: Any) -> "SchemaBuilder":
        self.inverted_index_config = ConfigurationBuilder.bm25_config(**kwargs)
        return self

    def build(self) -> Dict[str, Any]:
        SchemaValidator.validate_properties(self.properties)
        SchemaValidator.validate_configurations(
            {
                "vectorizer": self.vectorizer_config,
                "invertedIndexConfig": self.inverted_index_config,
                "vectorIndexConfig": self.vector_index_config,
            }
        )

        return {
            "class": self.class_name,
            "description": f"Schema for {self.class_name} collection",
            **self.vectorizer_config,
            "invertedIndexConfig": self.inverted_index_config,
            "vectorIndexConfig": self.vector_index_config,
            "replicationConfig": self.replication_config,
            "multiTenancyConfig": self.multi_tenancy_config,
            "shardingConfig": self.sharding_config,
            "properties": self.properties,
        }

    def _create_property(self, name: str, data_type: str, **kwargs: Any) -> Dict[str, Any]:
        property_def = {"name": name, "dataType": [data_type], **kwargs}
        return property_def
