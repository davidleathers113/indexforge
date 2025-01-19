"""Version history models.

This module defines the data models used for version history tracking.
Supports rich change tracking, diff storage, and reliability scoring.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from src.core.lineage.version.types import VersionChangeType


@dataclass
class Change:
    """Individual change record with detailed metadata.

    Attributes:
        change_type: Type of change (content, metadata, etc)
        description: Human readable description
        author: Who made the change
        id: Unique identifier for the change
        timestamp: When the change occurred
        diff: Optional diff of the changes
        metadata: Additional change-specific metadata
        parent_id: Optional ID of parent change
        reliability_score: Optional score indicating change reliability
    """

    change_type: VersionChangeType
    description: str
    author: str
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    diff: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    parent_id: UUID | None = None
    reliability_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert change to dictionary format.

        Returns:
            Dictionary representation of the change
        """
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "change_type": self.change_type.value,
            "description": self.description,
            "author": self.author,
            "diff": self.diff,
            "metadata": self.metadata,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "reliability_score": self.reliability_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Change":
        """Create change from dictionary format.

        Args:
            data: Dictionary representation of change

        Returns:
            New Change instance
        """
        return cls(
            id=UUID(data["id"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            change_type=VersionChangeType(data["change_type"]),
            description=data["description"],
            author=data["author"],
            diff=data.get("diff"),
            metadata=data.get("metadata", {}),
            parent_id=UUID(data["parent_id"]) if data.get("parent_id") else None,
            reliability_score=data.get("reliability_score"),
        )


@dataclass
class VersionTag:
    """Version tag information for marking significant points in history.

    Attributes:
        tag: Version tag string (e.g., "v1.0.0")
        timestamp: When the tag was created
        description: Description of what this version represents
        author: Who created the tag
        change_type: Type of change this version represents
        reliability_score: Score indicating version reliability
        changes: List of changes included in this version
        metadata: Additional version-specific metadata
    """

    tag: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    description: str = ""
    author: str = ""
    change_type: VersionChangeType = VersionChangeType.METADATA
    reliability_score: float = 1.0
    changes: list[Change] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_change(self, change: Change) -> None:
        """Add a change to this version.

        Args:
            change: Change to add
        """
        self.changes.append(change)
        # Update reliability score based on change
        if change.reliability_score is not None:
            self.reliability_score = min(self.reliability_score, change.reliability_score)

    def to_dict(self) -> dict[str, Any]:
        """Convert version tag to dictionary format.

        Returns:
            Dictionary representation of the version tag
        """
        return {
            "tag": self.tag,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "author": self.author,
            "change_type": self.change_type.value,
            "reliability_score": self.reliability_score,
            "changes": [c.to_dict() for c in self.changes],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VersionTag":
        """Create version tag from dictionary format.

        Args:
            data: Dictionary representation of version tag

        Returns:
            New VersionTag instance
        """
        tag = cls(
            tag=data["tag"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            description=data["description"],
            author=data["author"],
            change_type=VersionChangeType(data["change_type"]),
            reliability_score=data["reliability_score"],
            metadata=data.get("metadata", {}),
        )
        tag.changes = [Change.from_dict(c) for c in data.get("changes", [])]
        return tag
