"""Document lineage management for IndexForge.

This package provides functionality for:
- Document lineage tracking and validation
- Change history management
- Source information tracking
"""

from .base import ChangeType, DocumentLineage, SourceInfo
from .cache import LineageCache
from .manager import LineageManager


__all__ = [
    # Base types
    "ChangeType",
    "DocumentLineage",
    "SourceInfo",
    # Cache management
    "LineageCache",
    # Lineage management
    "LineageManager",
]
