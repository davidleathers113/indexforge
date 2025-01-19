"""Tenant-specific source tracking and configuration.

This module extends the base source tracking functionality with tenant-specific
features, ensuring proper isolation and configuration management per tenant.

Key Features:
    - Tenant-specific configuration storage
    - Isolated schema variations
    - Per-tenant custom properties
    - Tenant-aware validation
"""

import logging
from pathlib import Path
from typing import Any

from src.core.errors import ValidationError
from src.core.tracking.source.config import SourceConfig
from src.core.tracking.source.tracker import SourceTracker


class TenantSourceTracker(SourceTracker):
    """Manages tenant-specific source configurations and tracking.

    This class extends SourceTracker to provide tenant-specific functionality,
    ensuring proper isolation between different tenants' configurations and
    schema variations.

    Attributes:
        tenant_id: Unique identifier for the tenant
        source_type: Type of source being tracked
        config_dir: Base directory for configuration storage
        tenant_config_dir: Tenant-specific configuration directory

    Example:
        ```python
        # Initialize tracker for tenant's Word documents
        tracker = TenantSourceTracker("tenant123", "word")

        # Get tenant-specific schema
        schema = tracker.get_schema()

        # Update tenant's configuration
        tracker.update_config({
            "schema_variations": {
                "class": "WordDocument",
                "description": "Tenant-specific Word document"
            }
        })
        ```
    """

    def __init__(self, tenant_id: str, source_type: str, config_dir: str | None = None) -> None:
        """Initialize the tenant source tracker.

        Args:
            tenant_id: Unique identifier for the tenant
            source_type: Type of source to track
            config_dir: Optional base directory for configurations
        """
        self.tenant_id = tenant_id

        # Initialize base tracker with tenant-specific path
        base_config_dir = Path(config_dir) if config_dir else Path.home() / ".indexforge" / "config"
        tenant_config_dir = base_config_dir / "tenants" / tenant_id
        super().__init__(source_type, str(tenant_config_dir))

        self.logger = logging.getLogger(f"{__name__}.{tenant_id}")

    def _get_default_config(self) -> SourceConfig:
        """Create tenant-specific default configuration.

        Returns:
            SourceConfig: Default configuration for this tenant
        """
        config = super()._get_default_config()

        # Add tenant-specific metadata
        config.schema_variations.update(
            {
                "tenant_id": self.tenant_id,
                "class": f"Tenant{self.source_type.title()}Document",
                "description": f"Tenant-specific {self.source_type} document",
            }
        )

        return config

    def validate_schema(self) -> list[str]:
        """Validate tenant-specific schema.

        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = super().validate_schema()

        # Additional tenant-specific validation
        if "tenant_id" not in self.config.schema_variations:
            errors.append("Missing tenant_id in schema variations")
        elif self.config.schema_variations["tenant_id"] != self.tenant_id:
            errors.append(
                f"Schema tenant_id mismatch: {self.config.schema_variations['tenant_id']} "
                f"!= {self.tenant_id}"
            )

        return errors

    def get_tenant_info(self) -> dict[str, Any]:
        """Get tenant-specific information.

        Returns:
            Dict[str, Any]: Tenant information and configuration
        """
        return {
            "tenant_id": self.tenant_id,
            "source_type": self.source_type,
            "config_dir": str(self.config_dir),
            "schema_variations": self.config.schema_variations,
            "custom_properties": self.config.custom_properties,
        }

    def update_config(self, config_updates: dict[str, Any]) -> None:
        """Update tenant-specific configuration.

        Args:
            config_updates: Dictionary of configuration updates

        Raises:
            ValidationError: If updates would break tenant isolation
        """
        # Ensure tenant_id isn't changed
        if "schema_variations" in config_updates:
            variations = config_updates["schema_variations"]
            if "tenant_id" in variations and variations["tenant_id"] != self.tenant_id:
                raise ValidationError(
                    f"Cannot change tenant_id from {self.tenant_id} to {variations['tenant_id']}"
                )
            # Ensure tenant_id is preserved
            variations["tenant_id"] = self.tenant_id

        super().update_config(config_updates)
