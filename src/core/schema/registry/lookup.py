"""Schema lookup implementation.

This module provides efficient schema lookup functionality with support for
version resolution and dependency tracking.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from src.core.schema.base import SchemaType, SchemaVersion
from src.core.schema.schema import Schema


@dataclass
class LookupResult:
    """Result of a schema lookup operation."""

    schema: Optional[Schema]
    dependencies: Set[str]
    is_active: bool
    error: Optional[str] = None


class SchemaLookup:
    """Schema lookup implementation."""

    def __init__(self) -> None:
        """Initialize schema lookup."""
        self._type_index: Dict[SchemaType, Set[str]] = {t: set() for t in SchemaType}
        self._version_index: Dict[str, List[SchemaVersion]] = {}

    def index_schema(self, schema: Schema) -> None:
        """Index a schema for efficient lookup.

        Args:
            schema: Schema to index
        """
        # Update type index
        self._type_index[schema.schema_type].add(schema.name)

        # Update version index
        if schema.name not in self._version_index:
            self._version_index[schema.name] = []
        versions = self._version_index[schema.name]
        if schema.version not in versions:
            versions.append(schema.version)
            versions.sort(reverse=True)

    def find_by_type(self, schema_type: SchemaType) -> Set[str]:
        """Find all schema names of a given type.

        Args:
            schema_type: Type to search for

        Returns:
            Set of schema names
        """
        return self._type_index.get(schema_type, set())

    def find_latest_version(self, name: str) -> Optional[SchemaVersion]:
        """Find latest version of a schema.

        Args:
            name: Schema name

        Returns:
            Latest version if found, None otherwise
        """
        versions = self._version_index.get(name, [])
        return versions[0] if versions else None

    def find_compatible_version(
        self,
        name: str,
        min_version: Optional[SchemaVersion] = None,
        max_version: Optional[SchemaVersion] = None,
    ) -> Optional[SchemaVersion]:
        """Find compatible schema version.

        Args:
            name: Schema name
            min_version: Minimum required version
            max_version: Maximum allowed version

        Returns:
            Compatible version if found, None otherwise
        """
        versions = self._version_index.get(name, [])
        for version in versions:
            if min_version and version < min_version:
                continue
            if max_version and version > max_version:
                continue
            return version
        return None
