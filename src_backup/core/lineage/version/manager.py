"""Version history management.

This module provides the core functionality for managing version history.
Integrates with change tracking for detailed history.
"""

import logging
from uuid import UUID

from src.core.lineage.version.change_manager import ChangeManager
from src.core.lineage.version.models import VersionTag
from src.core.lineage.version.types import VersionChangeType, VersionTagError
from src.core.lineage.version.validation import VersionValidator
from src.core.storage.strategies.json_storage import JsonStorage


logger = logging.getLogger(__name__)


class VersionManager:
    """Manages version history for documents."""

    def __init__(self, storage: JsonStorage):
        """Initialize version manager.

        Args:
            storage: Storage strategy for persistence
        """
        self.storage = storage
        self.change_manager = ChangeManager(storage)
        self._tags: dict[UUID, dict[str, VersionTag]] = {}

    async def _load_tags(self, doc_id: UUID) -> None:
        """Load version tags for a document.

        Args:
            doc_id: Document ID to load tags for
        """
        key = f"versions:{doc_id}"
        data = await self.storage.load(key) or {}
        self._tags[doc_id] = {
            tag: VersionTag.from_dict(tag_data) for tag, tag_data in data.get("tags", {}).items()
        }

        # Validate loaded tags
        if self._tags[doc_id]:
            VersionValidator.validate_version_sequence(list(self._tags[doc_id].values()))

    async def create_tag(
        self,
        doc_id: UUID,
        tag: str,
        description: str,
        author: str,
        change_type: VersionChangeType,
        reliability_score: float | None = None,
    ) -> VersionTag:
        """Create a new version tag.

        Args:
            doc_id: Document ID to tag
            tag: Version tag string
            description: Tag description
            author: Who created the tag
            change_type: Type of change
            reliability_score: Optional reliability score

        Returns:
            The created version tag

        Raises:
            VersionTagError: If tag already exists
            VersionValidationError: If validation fails
        """
        if doc_id not in self._tags:
            await self._load_tags(doc_id)

        if tag in self._tags[doc_id]:
            raise VersionTagError(f"Version tag {tag} already exists")

        # Get recent changes to include in tag
        changes = await self.change_manager.get_changes(doc_id)

        version_tag = VersionTag(
            tag=tag,
            description=description,
            author=author,
            change_type=change_type,
            reliability_score=reliability_score,
            changes=changes,
        )

        # Validate before saving
        VersionValidator.validate_version_tag(version_tag)

        self._tags[doc_id][tag] = version_tag
        await self._persist_tags(doc_id)
        return version_tag

    async def get_tag(self, doc_id: UUID, tag: str) -> VersionTag:
        """Get a specific version tag.

        Args:
            doc_id: Document ID
            tag: Version tag to get

        Returns:
            The requested version tag

        Raises:
            VersionTagError: If tag doesn't exist
        """
        if doc_id not in self._tags:
            await self._load_tags(doc_id)

        if tag not in self._tags[doc_id]:
            raise VersionTagError(f"Version tag {tag} not found")

        return self._tags[doc_id][tag]

    async def get_tags(
        self,
        doc_id: UUID,
        change_type: VersionChangeType | None = None,
        author: str | None = None,
    ) -> list[VersionTag]:
        """Get version tags matching criteria.

        Args:
            doc_id: Document ID to get tags for
            change_type: Optional change type to filter by
            author: Optional author to filter by

        Returns:
            List of matching version tags
        """
        if doc_id not in self._tags:
            await self._load_tags(doc_id)

        tags = list(self._tags[doc_id].values())

        if change_type:
            tags = [t for t in tags if t.change_type == change_type]
        if author:
            tags = [t for t in tags if t.author == author]

        return sorted(tags, key=lambda x: x.timestamp)

    async def _persist_tags(self, doc_id: UUID) -> None:
        """Persist version tags to storage.

        Args:
            doc_id: Document ID to persist tags for
        """
        key = f"versions:{doc_id}"
        data = {"tags": {tag: version.to_dict() for tag, version in self._tags[doc_id].items()}}
        await self.storage.save(key, data)

        # Validate after loading from storage to ensure data integrity
        if self._tags[doc_id]:
            VersionValidator.validate_version_sequence(list(self._tags[doc_id].values()))
