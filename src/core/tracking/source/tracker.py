"""Source tracking and configuration management.

This module provides the SourceTracker class for managing source-specific
configurations, schema variations, and custom properties. It handles loading,
validation, and persistence of source configurations.

Key Features:
    - Source-specific schema variations
    - Custom property management
    - Vectorizer configuration
    - Cross-source mappings
    - Configuration persistence
    - Schema validation
"""

import json
import logging
from pathlib import Path
from typing import Any

from src.core.errors import ValidationError
from src.core.schema import Schema, SchemaStorage
from src.core.tracking.source.config import SourceConfig


class SourceTracker:
    """Manages source-specific configuration and schema variations.

    This class provides functionality for managing source-specific configurations,
    including schema variations, custom properties, and cross-source mappings.
    It handles loading, validation, and persistence of source configurations.

    Attributes:
        source_type: Type of source being tracked (e.g., "word", "pdf")
        config_dir: Directory for storing source configurations
        logger: Logger instance for tracking operations

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
            }
        })
        ```
    """

    def __init__(self, source_type: str, config_dir: str | None = None) -> None:
        """Initialize the source tracker.

        Args:
            source_type: Type of source to track (e.g., "word", "pdf")
            config_dir: Optional directory for storing configurations
        """
        self.source_type = source_type
        self.config_dir = Path(config_dir) if config_dir else Path.home() / ".indexforge" / "config"
        self.logger = logging.getLogger(__name__)

        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load or create source configuration
        self.config = self._load_source_config()

        # Initialize schema storage
        self.schema_storage = SchemaStorage()

    def _load_source_config(self) -> SourceConfig:
        """Load source configuration from file or create default.

        Returns:
            SourceConfig: Configuration for this source type
        """
        config_path = self.config_dir / f"{self.source_type}_config.json"

        if config_path.exists():
            try:
                with open(config_path) as f:
                    config_data = json.load(f)
                return SourceConfig(**config_data)
            except (json.JSONDecodeError, TypeError) as e:
                self.logger.error(f"Failed to load source config: {e}")
                return self._get_default_config()

        return self._get_default_config()

    def _get_default_config(self) -> SourceConfig:
        """Create default configuration for this source type.

        Returns:
            SourceConfig: Default configuration
        """
        return SourceConfig(
            schema_variations={
                "class": f"{self.source_type.title()}Document",
                "description": f"{self.source_type.title()} document source",
            },
            custom_properties={},
            vectorizer_settings={"model": "all-MiniLM-L6-v2", "poolingStrategy": "mean"},
            cross_source_mappings={},
        )

    def get_schema(self) -> dict[str, Any]:
        """Get source-specific schema with variations applied.

        Returns:
            Dict[str, Any]: Schema for this source type
        """
        base_schema = self.schema_storage.get_schema("document")
        if not base_schema:
            raise ValidationError("Base document schema not found")

        # Apply source-specific variations
        schema = Schema(base_schema)
        schema.update(self.config.schema_variations)

        # Add custom properties
        if self.config.custom_properties:
            schema.add_properties(self.config.custom_properties)

        return schema.to_dict()

    def get_custom_properties(self) -> dict[str, Any]:
        """Get custom properties for this source type.

        Returns:
            Dict[str, Any]: Custom property definitions
        """
        return self.config.custom_properties

    def get_cross_source_mappings(self) -> dict[str, str]:
        """Get mappings to other source types.

        Returns:
            Dict[str, str]: Cross-source mappings
        """
        return self.config.cross_source_mappings

    def validate_schema(self) -> list[str]:
        """Validate the source-specific schema.

        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []
        try:
            schema = self.get_schema()
            Schema(schema).validate()
        except ValidationError as e:
            errors.append(str(e))

        # Validate custom properties
        for prop_name, prop_def in self.config.custom_properties.items():
            if "dataType" not in prop_def:
                errors.append(f"Custom property '{prop_name}' missing dataType")
            if "description" not in prop_def:
                errors.append(f"Custom property '{prop_name}' missing description")

        return errors

    def update_config(self, config_updates: dict[str, Any]) -> None:
        """Update source configuration.

        Args:
            config_updates: Dictionary of configuration updates
        """
        # Update configuration
        for key, value in config_updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # Validate updated configuration
        errors = self.validate_schema()
        if errors:
            raise ValidationError(f"Invalid configuration: {'; '.join(errors)}")

        # Save updated configuration
        config_path = self.config_dir / f"{self.source_type}_config.json"
        with open(config_path, "w") as f:
            json.dump(vars(self.config), f, indent=2)
