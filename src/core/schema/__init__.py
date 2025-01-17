"""Schema management and validation for IndexForge.

This package provides functionality for:
- Schema definition and validation
- Schema versioning and compatibility
- Schema storage and registry management
"""

from .base import BaseSchema, SchemaType, ValidationError
from .schema import Schema
from .storage import SchemaStorage


__all__ = [
    # Base components
    "BaseSchema",
    "SchemaType",
    "ValidationError",
    # Schema management
    "Schema",
    "SchemaStorage",
]
