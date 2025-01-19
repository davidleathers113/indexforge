"""
Schema retrieval operations for Weaviate database.

This module provides functionality to retrieve schema configurations from
a Weaviate database instance.
"""

import logging

import weaviate


class SchemaRetriever:
    """Handles schema retrieval operations from Weaviate."""

    def __init__(self, client: weaviate.Client, class_name: str):
        self.client = client
        self.class_name = class_name
        self.logger = logging.getLogger(__name__)

    def get_schema(self) -> dict | None:
        """Retrieve the current schema configuration from Weaviate."""
        try:
            schema = self.client.schema.get()
            if not schema or "classes" not in schema:
                self.logger.warning("No schema or classes found in Weaviate")
                return None

            for cls in schema.get("classes", []):
                if cls.get("class") == self.class_name:
                    return cls

            self.logger.warning(f"Class {self.class_name} not found in schema")
            return None
        except Exception as e:
            self.logger.error(f"Error getting schema: {e!s}", exc_info=True)
            raise
