"""Version history package.

This package provides functionality for managing document version history.
"""

from src.core.lineage.version.manager import VersionManager
from src.core.lineage.version.models import VersionTag
from src.core.lineage.version.types import VersionChangeType, VersionError, VersionTagError

__all__ = [
    "VersionManager",
    "VersionTag",
    "VersionChangeType",
    "VersionError",
    "VersionTagError",
]
