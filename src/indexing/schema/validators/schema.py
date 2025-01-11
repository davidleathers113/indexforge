"""
Schema validation rules and functionality.

This module provides functions to validate Weaviate schema configurations
against requirements, including v4.x specific features.
"""

import logging
from typing import Dict, Set

logger = logging.getLogger(__name__)

# Required properties that must be present in the schema
REQUIRED_PROPERTIES: Set[str] = {
    "content_body",
    "content_summary",
    "content_title",
    "embedding",
    "timestamp_utc",
    "schema_version",
    "parent_id",
    "chunk_ids",
}


def validate_schema(schema: Dict) -> bool:
    """Validate base schema configuration."""
    try:
        # Basic validation
        if not schema.get("class"):
            logger.error("Missing class name in schema")
            return False
        if not schema.get("properties"):
            logger.error("Missing properties in schema")
            return False
        if not schema.get("vectorizer"):
            logger.error("Missing vectorizer in schema")
            return False

        # Validate required properties
        schema_props = {p["name"] for p in schema.get("properties", [])}
        if not REQUIRED_PROPERTIES.issubset(schema_props):
            missing_props = REQUIRED_PROPERTIES - schema_props
            logger.error(f"Missing required properties: {missing_props}")
            return False

        # Validate property types
        for prop in schema["properties"]:
            if not prop.get("dataType"):
                logger.error(f"Missing dataType for property {prop['name']}")
                return False
            if prop["name"] == "embedding" and "vector" not in prop["dataType"]:
                logger.error(f"Invalid dataType for embedding property: {prop['dataType']}")
                return False

        return True
    except Exception as e:
        logger.error(f"Error validating schema: {str(e)}", exc_info=True)
        return False


def validate_vectorizer_config(config: Dict) -> bool:
    """Validate vectorizer configuration for v4.x."""
    try:
        if not config:
            return True  # Optional config

        required = {"vectorizer", "model", "poolingStrategy"}
        if not all(key in config for key in required):
            logger.error(f"Missing required vectorizer config keys: {required - config.keys()}")
            return False

        return True
    except Exception as e:
        logger.error(f"Error validating vectorizer config: {str(e)}", exc_info=True)
        return False


def validate_compression_config(config: Dict) -> bool:
    """Validate vector compression configuration for v4.x."""
    try:
        if not config:
            return True  # Optional config

        if config.get("pq", {}).get("enabled"):
            pq_config = config["pq"]
            if not all(key in pq_config for key in {"segments", "encoder"}):
                logger.error("Missing required PQ compression config keys")
                return False

        if config.get("bq", {}).get("enabled"):
            bq_config = config["bq"]
            if "type" not in bq_config:
                logger.error("Missing required BQ compression type")
                return False

        return True
    except Exception as e:
        logger.error(f"Error validating compression config: {str(e)}", exc_info=True)
        return False


def validate_multimodal_config(config: Dict) -> bool:
    """Validate multimodal configuration for v4.x."""
    try:
        if not config:
            return True  # Optional config

        required = {"model", "imageFields", "textFields"}
        if not all(key in config for key in required):
            logger.error(f"Missing required multimodal config keys: {required - config.keys()}")
            return False

        return True
    except Exception as e:
        logger.error(f"Error validating multimodal config: {str(e)}", exc_info=True)
        return False
