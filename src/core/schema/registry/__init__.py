"""Schema registry module for managing and retrieving schema definitions.

This module provides centralized schema management functionality, including:
- Schema registration and lookup
- Schema caching and invalidation
- Schema version tracking
- Schema dependency resolution
"""

from .cache import CacheConfig, SchemaCache
from .lookup import LookupResult, SchemaLookup
from .manager import SchemaRegistry, SchemaRegistryError


__all__ = [
    "CacheConfig",
    "LookupResult",
    "SchemaCache",
    "SchemaLookup",
    "SchemaRegistry",
    "SchemaRegistryError",
]
