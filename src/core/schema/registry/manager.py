"""Schema registry manager implementation.

This module provides the core schema registry functionality for managing schema
definitions across the system.
"""


from src.core.schema.base import SchemaType, SchemaVersion
from src.core.schema.registry.cache import CacheConfig, SchemaCache
from src.core.schema.registry.lookup import SchemaLookup
from src.core.schema.schema import Schema
from src.core.schema.storage import SchemaStorage


class SchemaRegistryError(Exception):
    """Base exception for schema registry errors."""

    pass


class CircularDependencyError(SchemaRegistryError):
    """Raised when circular dependencies are detected."""

    pass


class SchemaRegistry:
    """Central registry for managing schema definitions."""

    def __init__(
        self,
        storage: SchemaStorage,
        cache_config: CacheConfig | None = None,
    ) -> None:
        """Initialize schema registry.

        Args:
            storage: Schema storage backend
            cache_config: Optional cache configuration
        """
        self.storage = storage
        self._cache = SchemaCache(config=cache_config) if cache_config else None
        self._lookup = SchemaLookup()
        self._active_schemas: dict[str, Schema] = {}
        self._dependencies: dict[str, set[str]] = {}

    async def register_schema(
        self,
        schema: Schema,
        make_active: bool = True,
        update_dependencies: bool = True,
    ) -> None:
        """Register a new schema or update existing one.

        Args:
            schema: Schema to register
            make_active: Whether to make this schema active
            update_dependencies: Whether to update schema dependencies

        Raises:
            SchemaRegistryError: If schema registration fails
        """
        try:
            # Store schema
            self.storage.store_schema(schema, make_active=make_active)

            # Update cache if enabled
            if self._cache and make_active:
                await self._cache.set(schema.name, schema)

            # Update active schemas
            if make_active:
                self._active_schemas[schema.name] = schema

            # Update dependencies
            if update_dependencies:
                self._update_dependencies(schema)

        except Exception as e:
            raise SchemaRegistryError(f"Failed to register schema: {e}") from e

    async def get_schema(
        self,
        name: str,
        version: SchemaVersion | None = None,
        use_cache: bool = True,
    ) -> Schema | None:
        """Retrieve a schema by name and optional version.

        Args:
            name: Schema name
            version: Optional specific version
            use_cache: Whether to check cache first

        Returns:
            Schema if found, None otherwise
        """
        # Check cache first if enabled and requested
        if use_cache and self._cache:
            cached = await self._cache.get(name)
            if cached:
                return cached

        # Check active schemas
        if not version and name in self._active_schemas:
            return self._active_schemas[name]

        # Fall back to storage
        schema = self.storage.get_schema(name, version)
        if schema and self._cache:
            await self._cache.set(name, schema)
        return schema

    def list_schemas(
        self,
        schema_type: SchemaType | None = None,
        include_inactive: bool = False,
    ) -> list[Schema]:
        """List available schemas.

        Args:
            schema_type: Optional filter by schema type
            include_inactive: Whether to include inactive schemas

        Returns:
            List of matching schemas
        """
        schemas = []
        for metadata in self.storage.list_schemas(schema_type):
            if include_inactive or metadata.is_active:
                schema = self.storage.get_schema(metadata.name)
                if schema:
                    schemas.append(schema)
        return schemas

    def get_dependencies(self, name: str) -> set[str]:
        """Get dependencies for a schema.

        Args:
            name: Schema name

        Returns:
            Set of schema names this schema depends on
        """
        return self._dependencies.get(name, set())

    def _update_dependencies(self, schema: Schema) -> None:
        """Update dependency tracking for a schema.

        This method extracts and validates schema dependencies, including:
        - Field references to other schemas
        - Parent/child relationships
        - Cross-schema validations
        - Source-specific dependencies

        Args:
            schema: Schema to update dependencies for

        Raises:
            CircularDependencyError: If circular dependencies are detected
        """
        deps = set()

        # Extract field references
        for field in schema.fields.values():
            # Check for schema references in field types
            if field.type == "schema_ref":
                if not field.ref_schema:
                    raise SchemaRegistryError(f"Missing schema reference in field {field.name}")
                deps.add(field.ref_schema)

            # Check for array/object fields that reference other schemas
            if field.type in ("array", "object") and field.items_schema:
                deps.add(field.items_schema)

        # Extract parent schema if specified
        if schema.parent_schema:
            deps.add(schema.parent_schema)

        # Extract validation dependencies
        if schema.validation_schemas:
            deps.update(schema.validation_schemas)

        # Check for circular dependencies
        visited = {schema.name}
        stack = list(deps)

        while stack:
            dep_name = stack.pop()
            if dep_name in visited:
                path = " -> ".join(visited) + " -> " + dep_name
                raise CircularDependencyError(f"Circular dependency detected: {path}")

            visited.add(dep_name)
            if dep_name in self._dependencies:
                stack.extend(self._dependencies[dep_name])

        # Update dependencies
        self._dependencies[schema.name] = deps

    async def invalidate_cache(self, name: str) -> None:
        """Invalidate cache entry for a schema.

        Args:
            name: Schema name to invalidate
        """
        if self._cache:
            await self._cache.delete(name)
        if name in self._active_schemas:
            del self._active_schemas[name]
