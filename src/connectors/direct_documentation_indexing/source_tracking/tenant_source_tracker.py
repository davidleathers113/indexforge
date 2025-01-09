"""
Multi-tenant source configuration and schema management.

This module extends the base source tracking functionality to support
multi-tenancy, allowing different tenants to have customized configurations,
schema variations, and isolation levels. It provides features for managing
tenant-specific overrides and enforcing tenant isolation policies.

Key Features:
    - Multi-tenant support
    - Tenant-specific schema overrides
    - Custom property definitions per tenant
    - Configurable isolation levels
    - Cross-tenant search capabilities
    - Tenant-specific vectorizer settings
    - Configuration persistence

Example:
    ```python
    from pathlib import Path

    # Initialize tenant-specific tracker
    tracker = TenantSourceTracker(
        tenant_id="tenant123",
        source_type="pdf",
        config_dir="/path/to/configs",
        tenant_config_dir="/path/to/tenant/configs"
    )

    # Get tenant-specific schema
    schema = tracker.get_schema()

    # Update tenant configuration
    tracker.update_tenant_config({
        "schema_overrides": {
            "class": "CustomPDFDocument",
            "description": "Tenant-specific PDF document"
        },
        "isolation_level": "strict",
        "cross_tenant_search": False
    })

    # Get search filters for tenant isolation
    filters = tracker.get_search_filters()
    ```
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .source_tracker import SourceTracker

logger = logging.getLogger(__name__)


@dataclass
class TenantConfig:
    """
    Configuration for a specific tenant.

    This class holds configuration settings specific to a tenant,
    including schema overrides, property customizations, and
    isolation settings.

    Attributes:
        tenant_id: Unique identifier for the tenant
        schema_overrides: Tenant-specific schema modifications
        property_overrides: Custom property definitions
        vectorizer_overrides: Custom vectorizer settings
        cross_tenant_search: Whether cross-tenant search is enabled
        isolation_level: Level of tenant isolation (strict/flexible)

    Example:
        ```python
        config = TenantConfig(
            tenant_id="tenant123",
            schema_overrides={
                "class": "CustomDocument",
                "description": "Tenant-specific document"
            },
            property_overrides={
                "custom_field": {
                    "dataType": ["text"],
                    "description": "Tenant-specific field"
                }
            },
            vectorizer_overrides={
                "model": "tenant-specific-model",
                "poolingStrategy": "cls"
            },
            cross_tenant_search=False,
            isolation_level="strict"
        )
        ```
    """

    tenant_id: str
    schema_overrides: Dict[str, Any]  # Tenant-specific schema overrides
    property_overrides: Dict[str, Any]  # Tenant-specific property overrides
    vectorizer_overrides: Dict[str, Any]  # Tenant-specific vectorizer settings
    cross_tenant_search: bool  # Whether cross-tenant search is enabled
    isolation_level: str  # Level of tenant isolation (strict, flexible)


class TenantSourceTracker(SourceTracker):
    """
    Extends SourceTracker to support multi-tenancy.

    This class enhances the base SourceTracker with multi-tenant capabilities,
    allowing different tenants to have customized configurations while
    maintaining proper isolation between tenants.

    Attributes:
        tenant_id: Identifier for the current tenant
        tenant_config_dir: Directory for tenant configurations
        tenant_config: Current tenant configuration

    Example:
        ```python
        # Initialize tracker for a tenant
        tracker = TenantSourceTracker(
            tenant_id="tenant123",
            source_type="pdf"
        )

        # Get tenant-specific schema
        schema = tracker.get_schema()

        # Check isolation level
        if tracker.get_isolation_level() == "strict":
            print("Strict tenant isolation enforced")

        # Get search filters
        filters = tracker.get_search_filters()
        print(f"Tenant filters: {filters}")
        ```
    """

    def __init__(
        self,
        tenant_id: str,
        source_type: str,
        config_dir: Optional[str] = None,
        tenant_config_dir: Optional[str] = None,
    ):
        """
        Initialize tenant-aware source tracker.

        Args:
            tenant_id: Unique identifier for the tenant
            source_type: The type of source (e.g., 'word', 'excel', 'pdf')
            config_dir: Optional directory containing source configurations
            tenant_config_dir: Optional directory containing tenant configurations

        Example:
            ```python
            # Use default config directories
            tracker = TenantSourceTracker(
                tenant_id="tenant123",
                source_type="pdf"
            )

            # Use custom config directories
            tracker = TenantSourceTracker(
                tenant_id="tenant123",
                source_type="pdf",
                config_dir="/path/to/source/configs",
                tenant_config_dir="/path/to/tenant/configs"
            )
            ```
        """
        super().__init__(source_type, config_dir)
        self.tenant_id = tenant_id
        self.tenant_config_dir = (
            Path(tenant_config_dir)
            if tenant_config_dir
            else Path(__file__).parent / "tenant_configs"
        )
        self.tenant_config = self._load_tenant_config()

    def _load_tenant_config(self) -> TenantConfig:
        """
        Load tenant-specific configuration.

        Returns:
            TenantConfig object with loaded or default configuration

        Note:
            If config file exists, loads from file
            If file doesn't exist or has errors, uses default config
        """
        config_path = self.tenant_config_dir / f"{self.tenant_id}_config.json"

        try:
            if config_path.exists():
                with open(config_path, "r") as f:
                    config_data = json.load(f)
                    return TenantConfig(**config_data)
            else:
                logger.warning(f"No config found for tenant {self.tenant_id}, using defaults")
                return self._get_default_tenant_config()
        except Exception as e:
            logger.error(f"Error loading tenant config: {e}")
            return self._get_default_tenant_config()

    def _get_default_tenant_config(self) -> TenantConfig:
        """
        Get default configuration for the tenant.

        Returns:
            TenantConfig object with default settings

        Note:
            Used when no configuration file exists or when loading fails
        """
        return TenantConfig(
            tenant_id=self.tenant_id,
            schema_overrides={},
            property_overrides={},
            vectorizer_overrides={},
            cross_tenant_search=False,
            isolation_level="strict",
        )

    def get_schema(self) -> Dict[str, Any]:
        """
        Get tenant-specific schema, overriding source schema where specified.

        This method combines the base source schema with tenant-specific
        overrides and adds necessary tenant isolation properties.

        Returns:
            Dictionary containing the complete schema definition

        Example:
            ```python
            # Get tenant-specific schema
            schema = tracker.get_schema()

            # Access schema components
            class_name = schema["class"]
            properties = schema["properties"]
            tenant_props = schema["properties"]["tenant_id"]
            ```
        """
        base_schema = super().get_schema()

        # Apply tenant-specific overrides
        if self.tenant_config.schema_overrides:
            base_schema.update(self.tenant_config.schema_overrides)

        # Add tenant-specific properties
        if self.tenant_config.property_overrides:
            base_schema["properties"].update(self.tenant_config.property_overrides)

        # Add tenant isolation properties
        base_schema["properties"]["tenant_id"] = {
            "dataType": ["text"],
            "description": "Tenant identifier for isolation",
            "indexInverted": True,
        }

        # Apply vectorizer overrides
        if self.tenant_config.vectorizer_overrides:
            base_schema["moduleConfig"]["text2vec-transformers"].update(
                self.tenant_config.vectorizer_overrides
            )

        return base_schema

    def validate_schema(self) -> List[str]:
        """
        Validate the tenant-specific schema configuration.

        This method performs validation of the schema configuration,
        including tenant-specific overrides and isolation properties.

        Returns:
            List of validation error messages, empty if valid

        Example:
            ```python
            # Validate tenant schema
            errors = tracker.validate_schema()
            if errors:
                print("Schema validation failed:")
                for error in errors:
                    print(f"- {error}")
            else:
                print("Schema is valid")
            ```
        """
        errors = super().validate_schema()

        # Additional tenant-specific validation
        schema = self.get_schema()

        # Validate tenant isolation
        if "tenant_id" not in schema["properties"]:
            errors.append("Missing tenant_id property for isolation")

        # Validate tenant-specific overrides
        if self.tenant_config.schema_overrides:
            if not isinstance(self.tenant_config.schema_overrides, dict):
                errors.append("Invalid schema overrides format")

        if self.tenant_config.property_overrides:
            if not isinstance(self.tenant_config.property_overrides, dict):
                errors.append("Invalid property overrides format")

        return errors

    def update_tenant_config(self, config_updates: Dict[str, Any]) -> None:
        """
        Update tenant-specific configuration.

        This method updates the tenant configuration with new values and
        persists the changes to disk.

        Args:
            config_updates: Dictionary of configuration updates

        Example:
            ```python
            # Update tenant configuration
            tracker.update_tenant_config({
                "schema_overrides": {
                    "class": "CustomDocument",
                    "description": "Updated document class"
                },
                "cross_tenant_search": True,
                "isolation_level": "flexible"
            })
            ```
        """
        try:
            # Update config object
            for key, value in config_updates.items():
                if hasattr(self.tenant_config, key):
                    setattr(self.tenant_config, key, value)

            # Save to file
            config_path = self.tenant_config_dir / f"{self.tenant_id}_config.json"
            config_data = {
                "tenant_id": self.tenant_config.tenant_id,
                "schema_overrides": self.tenant_config.schema_overrides,
                "property_overrides": self.tenant_config.property_overrides,
                "vectorizer_overrides": self.tenant_config.vectorizer_overrides,
                "cross_tenant_search": self.tenant_config.cross_tenant_search,
                "isolation_level": self.tenant_config.isolation_level,
            }

            self.tenant_config_dir.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"Updated configuration for tenant {self.tenant_id}")
        except Exception as e:
            logger.error(f"Error updating tenant config: {e}")
            raise

    def get_search_filters(self) -> Dict[str, Any]:
        """
        Get search filters for tenant isolation.

        This method returns filters that should be applied to searches
        to maintain proper tenant isolation.

        Returns:
            Dictionary containing search filters

        Example:
            ```python
            # Get tenant-specific filters
            filters = tracker.get_search_filters()

            # Use in search query
            results = search_documents(query="example", filters=filters)
            ```
        """
        filters = {"tenant_id": self.tenant_id}

        if self.tenant_config.cross_tenant_search:
            # Add any additional cross-tenant search logic here
            pass

        return filters

    def is_cross_tenant_search_enabled(self) -> bool:
        """
        Check if cross-tenant search is enabled.

        Returns:
            True if cross-tenant search is enabled, False otherwise

        Example:
            ```python
            if tracker.is_cross_tenant_search_enabled():
                print("Cross-tenant search is enabled")
                filters = {}  # No tenant isolation
            else:
                filters = tracker.get_search_filters()
            ```
        """
        return self.tenant_config.cross_tenant_search

    def get_isolation_level(self) -> str:
        """
        Get the tenant isolation level.

        Returns:
            String indicating isolation level ('strict' or 'flexible')

        Example:
            ```python
            level = tracker.get_isolation_level()
            if level == "strict":
                print("Strict tenant isolation enforced")
            else:
                print("Flexible tenant isolation enabled")
            ```
        """
        return self.tenant_config.isolation_level
