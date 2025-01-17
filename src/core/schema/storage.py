"""Schema storage implementation for IndexForge.

This module provides persistent storage for schema definitions, including
versioning support and efficient retrieval.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from pydantic import BaseModel

from .base import SchemaType, SchemaVersion
from .schema import Schema


class SchemaMetadata(BaseModel):
    """Metadata for stored schemas."""

    name: str
    version: SchemaVersion
    schema_type: SchemaType
    description: str = ""
    created_at: str
    is_active: bool = True
    dependencies: Set[str] = set()


class SchemaStorage:
    """Persistent storage for schema definitions."""

    def __init__(self, storage_dir: Path):
        """Initialize schema storage.

        Args:
            storage_dir: Directory for storing schema definitions
        """
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_cache: Dict[str, SchemaMetadata] = {}
        self._schema_cache: Dict[str, Schema] = {}
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load schema metadata from storage."""
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    metadata = SchemaMetadata(**data["metadata"])
                    self._metadata_cache[metadata.name] = metadata
            except Exception as e:
                # Log error but continue loading other schemas
                print(f"Error loading schema metadata from {file_path}: {e}")

    def store_schema(self, schema: Schema, make_active: bool = True) -> None:
        """Store a schema definition.

        Args:
            schema: Schema to store
            make_active: Whether to mark this schema as the active version
        """
        # Create metadata
        metadata = SchemaMetadata(
            name=schema.name,
            version=schema.version,
            schema_type=schema.schema_type,
            description=schema.description,
            created_at=schema.version.created_at.isoformat(),
            is_active=make_active,
            dependencies=set(),  # TODO: Extract dependencies from schema
        )

        # Prepare storage data
        storage_data = {"metadata": metadata.dict(), "schema": schema.to_dict()}

        # Store to file
        file_path = self._get_schema_path(schema.name, schema.version)
        with open(file_path, "w") as f:
            json.dump(storage_data, f, indent=2)

        # Update cache
        self._metadata_cache[schema.name] = metadata
        self._schema_cache[schema.name] = schema

        # If making active, deactivate other versions
        if make_active:
            self._deactivate_other_versions(schema.name, schema.version)

    def get_schema(self, name: str, version: Optional[SchemaVersion] = None) -> Optional[Schema]:
        """Retrieve a schema definition.

        Args:
            name: Schema name
            version: Optional specific version to retrieve, otherwise gets active version

        Returns:
            Schema if found, None otherwise
        """
        # Check cache first
        if name in self._schema_cache and (
            not version or self._metadata_cache[name].version == version
        ):
            return self._schema_cache[name]

        # Find schema file
        schema_path = None
        if version:
            schema_path = self._get_schema_path(name, version)
        else:
            # Find active version
            metadata = self._metadata_cache.get(name)
            if metadata and metadata.is_active:
                schema_path = self._get_schema_path(name, metadata.version)

        if not schema_path or not schema_path.exists():
            return None

        # Load schema
        try:
            with open(schema_path, "r") as f:
                data = json.load(f)
                schema = Schema.from_dict(data["schema"])
                self._schema_cache[name] = schema
                return schema
        except Exception as e:
            print(f"Error loading schema {name}: {e}")
            return None

    def list_schemas(self, schema_type: Optional[SchemaType] = None) -> List[SchemaMetadata]:
        """List available schemas.

        Args:
            schema_type: Optional filter by schema type

        Returns:
            List of schema metadata
        """
        schemas = list(self._metadata_cache.values())
        if schema_type:
            schemas = [s for s in schemas if s.schema_type == schema_type]
        return sorted(schemas, key=lambda s: (s.name, s.version))

    def get_schema_versions(self, name: str) -> List[SchemaVersion]:
        """Get all versions of a schema.

        Args:
            name: Schema name

        Returns:
            List of versions, sorted newest to oldest
        """
        versions = []
        for file_path in self.storage_dir.glob(f"{name}_*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    metadata = SchemaMetadata(**data["metadata"])
                    versions.append(metadata.version)
            except Exception as e:
                print(f"Error loading schema version from {file_path}: {e}")
        return sorted(versions, reverse=True)

    def delete_schema(self, name: str, version: Optional[SchemaVersion] = None) -> bool:
        """Delete a schema definition.

        Args:
            name: Schema name
            version: Optional specific version to delete, otherwise deletes all versions

        Returns:
            True if schema was deleted, False otherwise
        """
        if version:
            # Delete specific version
            file_path = self._get_schema_path(name, version)
            if file_path.exists():
                file_path.unlink()
                if name in self._schema_cache:
                    del self._schema_cache[name]
                if name in self._metadata_cache:
                    del self._metadata_cache[name]
                return True
            return False
        else:
            # Delete all versions
            deleted = False
            for file_path in self.storage_dir.glob(f"{name}_*.json"):
                file_path.unlink()
                deleted = True
            if deleted:
                if name in self._schema_cache:
                    del self._schema_cache[name]
                if name in self._metadata_cache:
                    del self._metadata_cache[name]
            return deleted

    def _get_schema_path(self, name: str, version: SchemaVersion) -> Path:
        """Get file path for a schema version.

        Args:
            name: Schema name
            version: Schema version

        Returns:
            Path to schema file
        """
        return self.storage_dir / f"{name}_{version.major}.{version.minor}.{version.patch}.json"

    def _deactivate_other_versions(self, name: str, active_version: SchemaVersion) -> None:
        """Deactivate all other versions of a schema.

        Args:
            name: Schema name
            active_version: Version to keep active
        """
        for file_path in self.storage_dir.glob(f"{name}_*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    metadata = SchemaMetadata(**data["metadata"])
                    if metadata.version != active_version:
                        metadata.is_active = False
                        data["metadata"] = metadata.dict()
                        with open(file_path, "w") as f:
                            json.dump(data, f, indent=2)
            except Exception as e:
                print(f"Error updating schema metadata in {file_path}: {e}")
