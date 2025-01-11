"""
Schema validation coordinator for Weaviate v4.x.

This module coordinates schema validation operations, supporting new features
like multimodal data, PQ/BQ compression, and enhanced vector configurations.
"""

import logging
from typing import Dict, Optional, Union

import weaviate
from weaviate.collections import Collection

from .schema_retriever import SchemaRetriever
from .schema_version_checker import SchemaVersionChecker
from .validators.document import validate_document_fields
from .validators.schema import (
    validate_compression_config,
    validate_multimodal_config,
    validate_schema,
    validate_vectorizer_config,
)


class SchemaValidator:
    """Coordinates schema validation for Weaviate v4.x."""

    def __init__(self, client: Union[weaviate.Client, Collection], class_name: str):
        """Initialize with either v3 Client or v4 Collection."""
        self.retriever = SchemaRetriever(client, class_name)
        self.version_checker = SchemaVersionChecker(self.retriever)
        self.logger = logging.getLogger(__name__)

    def get_schema(self) -> Optional[Dict]:
        """Get current schema configuration."""
        return self.retriever.get_schema()

    def check_schema_version(self) -> bool:
        """Check schema version compatibility."""
        return self.version_checker.check_schema_version()

    def validate_schema(self, schema: Dict) -> bool:
        """Validate complete schema configuration."""
        if not validate_schema(schema):
            return False

        # Validate v4.x specific configurations
        configs_valid = all(
            [
                validate_vectorizer_config(schema.get("vectorizer_config", {})),
                validate_compression_config(schema.get("vector_index_config", {})),
                validate_multimodal_config(schema.get("multimodal_config", {})),
            ]
        )

        return configs_valid

    @staticmethod
    def validate_object(
        doc: Dict,
        custom_fields: Optional[Dict] = None,
        doc_id: Optional[str] = None,
        strict: bool = True,
    ) -> None:
        """Validate a document object."""
        validate_document_fields(doc, custom_fields, doc_id, strict)
