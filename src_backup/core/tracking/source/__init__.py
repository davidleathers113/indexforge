"""Source tracking and configuration management for IndexForge.

This package provides functionality for:
- Source-specific configuration management
- Schema variations and validation
- Custom property handling
- Cross-source mappings
- Tenant-specific tracking
"""

from .config import SourceConfig
from .tenant import TenantSourceTracker
from .tracker import SourceTracker


__all__ = [
    # Configuration
    "SourceConfig",
    # Base tracking
    "SourceTracker",
    # Tenant tracking
    "TenantSourceTracker",
]
