"""Source configuration management.

This module provides the SourceConfig dataclass for managing source-specific
configuration settings, including schema variations, custom properties,
vectorizer settings, and cross-source mappings.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class SourceConfig:
    """Configuration for a specific source type.

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
