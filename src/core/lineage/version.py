"""Version history management for document lineage.

This module extends the core lineage functionality with version tagging,
reliability scoring, and detailed change tracking capabilities.

Example:
    ```python
    version_manager = VersionManager(storage)

    # Create a version tag
    tag = await version_manager.create_tag(
        doc_id=doc_id,
        tag="v1.0.0",
        description="Initial release",
        author="john.doe",
        change_type=VersionChangeType.SCHEMA,
        reliability_score=0.95
    )

    # Get version history
    tags = await version_manager.get_tags(doc_id)
    ```
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from src.core.storage.strategies.json_storage import JsonStorageStrategy

logger = logging.getLogger(__name__)


class VersionError(Exception):
    """Base exception for version-related errors."""


class VersionTagError(VersionError):
    """Error related to version tag operations."""


class VersionChangeType(Enum):
    """Types of version changes.

    Attributes:
        SCHEMA: Changes to the data schema definition
        CONFIG: Changes to configuration settings
        CONTENT: Changes to document content
        METADATA: Changes to metadata fields
        PROPERTY: Changes to individual properties
        VECTORIZER: Changes to vectorizer settings
    """

    SCHEMA = "schema"
    CONFIG = "config"
    CONTENT = "content"
    METADATA = "metadata"
    PROPERTY = "property"
    VECTORIZER = "vectorizer"


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
        """Convert version tag to dictionary format.

        Returns:
            Dictionary representation of the version tag.
        """
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
        """Create a VersionTag instance from a dictionary.

        Args:
            data: Dictionary containing version tag data.

        Returns:
            New VersionTag instance.

        Raises:
            VersionTagError: If required fields are missing or invalid.
        """
        try:
            if isinstance(data.get("timestamp"), str):
                data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            if isinstance(data.get("change_type"), str):
                data["change_type"] = VersionChangeType(data["change_type"])
            return cls(**data)
        except (ValueError, TypeError, KeyError) as e:
            raise VersionTagError(f"Invalid version tag data: {e}") from e


class VersionManager:
    """Manages version history for documents.

    This class provides functionality for creating and retrieving version tags,
    managing version history, and maintaining version metadata.

    Attributes:
        storage: Storage strategy for persisting version data
        _tags: In-memory cache of version tags by document ID
    """

    def __init__(self, storage: JsonStorageStrategy):
        """Initialize version manager.

        Args:
            storage: Storage strategy for persisting version data
        """
        self.storage = storage
        self._tags: dict[UUID, dict[str, VersionTag]] = {}

    async def create_tag(
        self,
        doc_id: UUID,
        tag: str,
        description: str,
        author: str,
        change_type: VersionChangeType,
        reliability_score: Optional[float] = None,
    ) -> VersionTag:
        """Create a new version tag for a document.

        Args:
            doc_id: Document ID to create tag for
            tag: Version tag string (e.g., "v1.0.0")
            description: Description of what this version represents
            author: Who created the tag
            change_type: Type of change this version represents
            reliability_score: Optional score indicating version reliability

        Returns:
            Created version tag

        Raises:
            VersionTagError: If tag already exists or validation fails
        """
        try:
            if doc_id not in self._tags:
                await self._load_tags(doc_id)

            if tag in self._tags[doc_id]:
                raise VersionTagError(f"Version tag {tag} already exists for document {doc_id}")

            version_tag = VersionTag(
                tag=tag,
                description=description,
                author=author,
                change_type=change_type,
                reliability_score=reliability_score,
            )

            self._tags[doc_id][tag] = version_tag
            await self._save_tags(doc_id)
            return version_tag

        except Exception as e:
            logger.exception(f"Error creating version tag for document {doc_id}: {e}")
            raise VersionTagError(f"Failed to create version tag: {e}") from e

    async def get_tags(self, doc_id: UUID) -> list[VersionTag]:
        """Get all version tags for a document.

        Args:
            doc_id: Document ID to get tags for

        Returns:
            List of version tags ordered by timestamp

        Raises:
            VersionTagError: If loading tags fails
        """
        try:
            if doc_id not in self._tags:
                await self._load_tags(doc_id)
            return sorted(self._tags[doc_id].values(), key=lambda x: x.timestamp)
        except Exception as e:
            logger.exception(f"Error getting version tags for document {doc_id}: {e}")
            raise VersionTagError(f"Failed to get version tags: {e}") from e

    async def _load_tags(self, doc_id: UUID) -> None:
        """Load version tags from storage.

        Args:
            doc_id: Document ID to load tags for

        Raises:
            VersionTagError: If loading fails
        """
        try:
            data = await self.storage.load(f"version_tags_{doc_id}")
            self._tags[doc_id] = {
                tag_data["tag"]: VersionTag.from_dict(tag_data) for tag_data in data.get("tags", [])
            }
        except Exception as e:
            logger.exception(f"Error loading version tags for document {doc_id}: {e}")
            self._tags[doc_id] = {}

    async def _save_tags(self, doc_id: UUID) -> None:
        """Save version tags to storage.

        Args:
            doc_id: Document ID to save tags for

        Raises:
            VersionTagError: If saving fails
        """
        try:
            data = {"tags": [tag.to_dict() for tag in self._tags[doc_id].values()]}
            await self.storage.save(f"version_tags_{doc_id}", data)
        except Exception as e:
            logger.exception(f"Error saving version tags for document {doc_id}: {e}")
            raise VersionTagError(f"Failed to save version tags: {e}") from e
