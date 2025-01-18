"""Version history type definitions.

This module defines the core types and exceptions used in version history tracking.
"""

from enum import Enum


class VersionError(Exception):
    """Base exception for version-related errors."""


class VersionTagError(VersionError):
    """Error related to version tag operations."""


class VersionChangeType(Enum):
    """Types of version changes.

    Attributes:
        SCHEMA: Changes to the data schema definition
        CONFIG: Changes to configuration settings
        CONTENT: Changes to document content
        METADATA: Changes to metadata fields
        PROPERTY: Changes to individual properties
        VECTORIZER: Changes to vectorizer settings
    """

    SCHEMA = "schema"
    CONFIG = "config"
    CONTENT = "content"
    METADATA = "metadata"
    PROPERTY = "property"
    VECTORIZER = "vectorizer"
