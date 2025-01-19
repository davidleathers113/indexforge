"""
Schema version checking functionality.

This module provides functionality to check schema versions and determine
if migrations are needed.
"""

import logging

from .schema_retriever import SchemaRetriever


class SchemaVersionChecker:
    """Handles schema version checking operations."""

    def __init__(self, schema_retriever: SchemaRetriever):
        self.schema_retriever = schema_retriever
        self.logger = logging.getLogger(__name__)

    def check_schema_version(self) -> bool:
        """Check if the current schema version matches requirements."""
        try:
            schema = self.schema_retriever.get_schema()
            if not schema:
                self.logger.info("Schema doesn't exist, needs creation")
                return False

            properties = schema.get("properties", [])
            for prop in properties:
                if prop["name"] == "schema_version":
                    return True

            self.logger.warning("Schema version property not found")
            return False
        except Exception as e:
            self.logger.error(f"Error checking schema version: {e!s}", exc_info=True)
            raise
