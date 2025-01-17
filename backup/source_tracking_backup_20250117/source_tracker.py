"""
Source-specific configuration and schema management.

This module provides functionality for managing source-specific configurations,
schema variations, and custom properties. It handles loading, validation, and
persistence of source configurations, with support for custom vectorizer settings
and cross-source mappings.

Key Features:
    - Source-specific schema variations
    - Custom property management
    - Vectorizer configuration
    - Cross-source mappings
    - Configuration persistence
    - Schema validation

Example:
    ```python
    # Initialize tracker for Word documents
    tracker = SourceTracker("word")

    # Get source-specific schema
    schema = tracker.get_schema()

    # Update configuration
    tracker.update_config({
        "schema_variations": {
            "class": "WordDocument",
            "description": "Microsoft Word document"
        },
        "vectorizer_settings": {
            "model": "all-MiniLM-L6-v2",
            "poolingStrategy": "mean"
        }
    })

    # Validate schema
    errors = tracker.validate_schema()
    if not errors:
        print("Schema is valid")
    ```
"""

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class SourceConfig:
    """
    Configuration for a specific source type.

    This class holds configuration settings specific to a particular source type,
    including schema variations, custom properties, vectorizer settings, and
    mappings to other source types.

    Attributes:
        schema_variations: Custom schema settings for this source type
        custom_properties: Source-specific property definitions
        vectorizer_settings: Custom vectorizer configuration
        cross_source_mappings: Mappings to other source types

    Example:
        ```python
        config = SourceConfig(
            schema_variations={
                "class": "PDFDocument",
                "description": "PDF document source",
                "vectorizer": "text2vec-transformers"
            },
            custom_properties={
                "page_count": {
                    "dataType": ["int"],
                    "description": "Number of pages"
                }
            },
            vectorizer_settings={
                "model": "all-MiniLM-L6-v2",
                "poolingStrategy": "mean"
            },
            cross_source_mappings={
                "word": "document_id",
                "excel": "sheet_id"
            }
        )
        ```
    """

    schema_variations: dict[str, Any]  # Custom schema settings
    custom_properties: dict[str, Any]  # Source-specific properties
    vectorizer_settings: dict[str, Any]  # Custom vectorizer configuration
    cross_source_mappings: dict[str, str]  # Mappings to other sources


class SourceTracker:
    """
    Manages source-specific configurations and schema variations.

    This class handles loading, validation, and persistence of source-specific
    configurations. It provides methods for accessing and updating schema
    variations, custom properties, and vectorizer settings.

    Attributes:
        source_type: Type of source being tracked (e.g., 'pdf', 'word')
        config_dir: Directory containing source configurations
        config: Current source configuration

    Example:
        ```python
        # Initialize tracker
        tracker = SourceTracker("pdf")

        # Get schema with custom properties
        schema = tracker.get_schema()

        # Update vectorizer settings
        tracker.update_config({
            "vectorizer_settings": {
                "model": "all-MiniLM-L6-v2",
                "poolingStrategy": "cls"
            }
        })

        # Validate configuration
        errors = tracker.validate_schema()
        for error in errors:
            print(f"Validation error: {error}")
        ```
    """

    def __init__(self, source_type: str, config_dir: str | None = None):
        """
        Initialize source tracker for a specific source type.

        Args:
            source_type: The type of source (e.g., 'word', 'excel', 'pdf')
            config_dir: Optional directory containing source configurations.
                       If not provided, uses default directory in package.

        Example:
            ```python
            # Use default config directory
            pdf_tracker = SourceTracker("pdf")

            # Use custom config directory
            word_tracker = SourceTracker(
                source_type="word",
                config_dir="/path/to/configs"
            )
            ```
        """
        self.source_type = source_type
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent / "configs"
        self.config = self._load_source_config()

    def _load_source_config(self) -> SourceConfig:
        """
        Load source configuration from file or defaults.

        This method attempts to load source-specific configuration from a JSON file.
        If the file doesn't exist or there's an error loading it, falls back to
        default configuration.

        Returns:
            SourceConfig object with loaded or default configuration

        Raises:
            Exception: If there are errors reading or parsing the config file.
                      These are caught and logged, with defaults used as fallback.

        Note:
            This is called automatically during initialization and should not
            typically need to be called directly.
        """
        config_path = self.config_dir / f"{self.source_type}_config.json"

        try:
            if config_path.exists():
                with open(config_path) as f:
                    config_data = json.load(f)
                    return SourceConfig(**config_data)
            else:
                logger.warning(
                    f"No config found for source type {self.source_type}, using defaults"
                )
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading source config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> SourceConfig:
        """
        Get default configuration for the source type.

        This method returns a basic configuration with sensible defaults for
        schema variations, custom properties, and vectorizer settings.

        Returns:
            SourceConfig object with default settings

        Example:
            ```python
            tracker = SourceTracker("pdf")
            default_config = tracker._get_default_config()
            print(f"Default class: {default_config.schema_variations['class']}")
            ```
        """
        return SourceConfig(
            schema_variations={
                "class": f"{self.source_type.capitalize()}Document",
                "description": f"Document from {self.source_type} source",
                "vectorizer": "text2vec-transformers",
            },
            custom_properties={
                "source_metadata": {"dataType": ["text"], "description": "Source-specific metadata"}
            },
            vectorizer_settings={
                "model": "sentence-transformers-all-MiniLM-L6-v2",
                "poolingStrategy": "mean",
            },
            cross_source_mappings={},
        )

    def get_schema(self) -> dict[str, Any]:
        """
        Get the complete schema for this source type.

        This method returns a complete schema definition including class information,
        custom properties, and vectorizer configuration. The schema includes both
        source-specific properties and standard properties required for all sources.

        Returns:
            Dictionary containing the complete schema definition

        Example:
            ```python
            tracker = SourceTracker("pdf")
            schema = tracker.get_schema()

            # Access schema components
            class_name = schema["class"]
            properties = schema["properties"]
            vectorizer_config = schema["moduleConfig"]["text2vec-transformers"]
            ```
        """
        base_schema = {
            "class": self.config.schema_variations["class"],
            "description": self.config.schema_variations["description"],
            "vectorizer": self.config.schema_variations["vectorizer"],
            "properties": {
                **self.config.custom_properties,
                "content": {
                    "dataType": ["text"],
                    "description": "The main content of the document",
                    "vectorizePropertyName": True,
                },
                "source_id": {
                    "dataType": ["text"],
                    "description": "Unique identifier for the source",
                    "indexInverted": True,
                },
            },
            "moduleConfig": {"text2vec-transformers": self.config.vectorizer_settings},
        }
        return base_schema

    def get_custom_properties(self) -> dict[str, Any]:
        """
        Get custom properties for this source type.

        Returns:
            Dictionary of custom property definitions

        Example:
            ```python
            tracker = SourceTracker("pdf")
            props = tracker.get_custom_properties()
            for name, definition in props.items():
                print(f"Property {name}: {definition['description']}")
            ```
        """
        return self.config.custom_properties

    def get_cross_source_mappings(self) -> dict[str, str]:
        """
        Get mappings to other source types.

        Returns:
            Dictionary mapping source types to their ID fields

        Example:
            ```python
            tracker = SourceTracker("pdf")
            mappings = tracker.get_cross_source_mappings()
            if "word" in mappings:
                print(f"Maps to Word docs via: {mappings['word']}")
            ```
        """
        return self.config.cross_source_mappings

    def validate_schema(self) -> list[str]:
        """
        Validate the source schema configuration.

        This method performs basic validation of the schema configuration,
        checking for required fields and properties. It ensures that the
        schema meets minimum requirements for use in the system.

        Returns:
            List of validation error messages, empty if valid

        Example:
            ```python
            tracker = SourceTracker("pdf")
            errors = tracker.validate_schema()
            if errors:
                print("Schema validation failed:")
                for error in errors:
                    print(f"- {error}")
            else:
                print("Schema is valid")
            ```
        """
        errors = []
        schema = self.get_schema()

        # Basic validation checks
        if not schema.get("class"):
            errors.append("Missing class name in schema")
        if not schema.get("properties"):
            errors.append("Missing properties in schema")
        if not schema.get("moduleConfig"):
            errors.append("Missing moduleConfig in schema")

        # Validate required properties
        required_props = {"content", "source_id"}
        missing_props = required_props - set(schema["properties"].keys())
        if missing_props:
            errors.append(f"Missing required properties: {missing_props}")

        return errors

    def update_config(self, config_updates: dict[str, Any]) -> None:
        """
        Update source configuration.

        This method updates the source configuration with new values and persists
        the changes to disk. It handles partial updates, allowing you to update
        specific configuration sections without affecting others.

        Args:
            config_updates: Dictionary of configuration updates. Can include
                          updates for schema_variations, custom_properties,
                          vectorizer_settings, and cross_source_mappings.

        Raises:
            Exception: If there are errors updating or saving the configuration.
                      These are logged and re-raised to allow error handling.

        Example:
            ```python
            tracker = SourceTracker("pdf")

            # Update vectorizer settings
            tracker.update_config({
                "vectorizer_settings": {
                    "model": "all-MiniLM-L6-v2",
                    "poolingStrategy": "cls"
                }
            })

            # Add custom property
            tracker.update_config({
                "custom_properties": {
                    "page_count": {
                        "dataType": ["int"],
                        "description": "Number of pages"
                    }
                }
            })
            ```
        """
        try:
            # Update config object
            for key, value in config_updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            # Save to file
            config_path = self.config_dir / f"{self.source_type}_config.json"
            config_data = {
                "schema_variations": self.config.schema_variations,
                "custom_properties": self.config.custom_properties,
                "vectorizer_settings": self.config.vectorizer_settings,
                "cross_source_mappings": self.config.cross_source_mappings,
            }

            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"Updated configuration for source type {self.source_type}")
        except Exception as e:
            logger.error(f"Error updating source config: {e}")
            raise
