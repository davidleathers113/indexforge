"""Version history management.

This module provides the core functionality for managing version history.
"""

import logging
from typing import Optional
from uuid import UUID

from src.core.lineage.version.models import VersionTag
from src.core.lineage.version.types import VersionChangeType, VersionTagError
from src.core.storage.strategies.json_storage import JsonStorageStrategy

logger = logging.getLogger(__name__)


class VersionManager:
    """Manages version history for documents."""

    def __init__(self, storage: JsonStorageStrategy):
        """Initialize version manager."""
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
        """Create a new version tag for a document."""
        try:
            if doc_id not in self._tags:
                await self._load_tags(doc_id)

            if tag in self._tags[doc_id]:
                raise VersionTagError(f"Version tag {tag} already exists")

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
            logger.exception(f"Error creating version tag: {e}")
            raise VersionTagError(f"Failed to create version tag: {e}") from e

    async def get_tags(self, doc_id: UUID) -> list[VersionTag]:
        """Get all version tags for a document."""
        try:
            if doc_id not in self._tags:
                await self._load_tags(doc_id)
            return sorted(self._tags[doc_id].values(), key=lambda x: x.timestamp)
        except Exception as e:
            logger.exception(f"Error getting version tags: {e}")
            raise VersionTagError(f"Failed to get version tags: {e}") from e

    async def _load_tags(self, doc_id: UUID) -> None:
        """Load version tags from storage."""
        try:
            data = await self.storage.load(f"version_tags_{doc_id}")
            self._tags[doc_id] = {
                tag_data["tag"]: VersionTag.from_dict(tag_data) for tag_data in data.get("tags", [])
            }
        except Exception as e:
            logger.exception(f"Error loading version tags: {e}")
            self._tags[doc_id] = {}

    async def _save_tags(self, doc_id: UUID) -> None:
        """Save version tags to storage."""
        try:
            data = {"tags": [tag.to_dict() for tag in self._tags[doc_id].values()]}
            await self.storage.save(f"version_tags_{doc_id}", data)
        except Exception as e:
            logger.exception(f"Error saving version tags: {e}")
            raise VersionTagError(f"Failed to save version tags: {e}") from e
