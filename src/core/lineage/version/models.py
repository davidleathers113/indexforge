"""Version history models.

This module defines the data models used for version history tracking.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

from src.core.lineage.version.types import VersionChangeType, VersionTagError


@dataclass
class VersionTag:
    """Version tag information for marking significant points in history.

    Attributes:
        tag: Version tag string (e.g., "v1.0.0")
        timestamp: When the tag was created
        description: Description of what this version represents
        author: Who created the tag
        change_type: Type of change this version represents
        reliability_score: Optional score indicating version reliability
    """

    tag: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    description: str = ""
    author: str = ""
    change_type: VersionChangeType = VersionChangeType.METADATA
    reliability_score: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert version tag to dictionary format."""
        return {
            "tag": self.tag,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "author": self.author,
            "change_type": self.change_type.value,
            "reliability_score": self.reliability_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VersionTag":
        """Create a VersionTag instance from a dictionary."""
        try:
            if isinstance(data.get("timestamp"), str):
                data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            if isinstance(data.get("change_type"), str):
                data["change_type"] = VersionChangeType(data["change_type"])
            return cls(**data)
        except (ValueError, TypeError, KeyError) as e:
            raise VersionTagError(f"Invalid version tag data: {e}") from e
