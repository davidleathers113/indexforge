"""Change tracking management.

This module provides functionality for tracking detailed changes in document history.
Handles change records, diffs, and reliability scoring.
"""

from datetime import datetime
import logging
from typing import Any
from uuid import UUID

from src.core.lineage.version.models import Change
from src.core.lineage.version.types import VersionChangeType
from src.core.storage.strategies.json_storage import JsonStorage


logger = logging.getLogger(__name__)


class ChangeManager:
    """Manages detailed change tracking for documents."""

    def __init__(self, storage: JsonStorage):
        """Initialize change manager.

        Args:
            storage: Storage strategy for persisting changes
        """
        self.storage = storage
        self._changes: dict[UUID, list[Change]] = {}

    async def _load_changes(self, doc_id: UUID) -> None:
        """Load changes for a document from storage.

        Args:
            doc_id: Document ID to load changes for
        """
        key = f"changes:{doc_id}"
        data = await self.storage.load(key) or {}
        changes = [Change.from_dict(c) for c in data.get("changes", [])]
        self._changes[doc_id] = sorted(changes, key=lambda x: x.timestamp)

    async def record_change(
        self,
        doc_id: UUID,
        change_type: VersionChangeType,
        description: str,
        author: str,
        diff: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        parent_id: UUID | None = None,
        reliability_score: float | None = None,
    ) -> Change:
        """Record a new change.

        Args:
            doc_id: Document ID the change applies to
            change_type: Type of change
            description: Human readable description
            author: Who made the change
            diff: Optional diff of the changes
            metadata: Additional change metadata
            parent_id: Optional ID of parent change
            reliability_score: Optional reliability score

        Returns:
            The created change record
        """
        if doc_id not in self._changes:
            await self._load_changes(doc_id)

        change = Change(
            change_type=change_type,
            description=description,
            author=author,
            diff=diff,
            metadata=metadata or {},
            parent_id=parent_id,
            reliability_score=reliability_score,
        )

        self._changes[doc_id].append(change)
        await self._persist_changes(doc_id)
        return change

    async def get_changes(
        self,
        doc_id: UUID,
        since: datetime | None = None,
        change_types: list[VersionChangeType] | None = None,
        author: str | None = None,
    ) -> list[Change]:
        """Get changes matching the specified criteria.

        Args:
            doc_id: Document ID to get changes for
            since: Optional timestamp to filter changes from
            change_types: Optional list of change types to include
            author: Optional author to filter by

        Returns:
            List of matching changes
        """
        if doc_id not in self._changes:
            await self._load_changes(doc_id)

        changes = self._changes[doc_id]

        if since:
            changes = [c for c in changes if c.timestamp >= since]
        if change_types:
            changes = [c for c in changes if c.change_type in change_types]
        if author:
            changes = [c for c in changes if c.author == author]

        return sorted(changes, key=lambda x: x.timestamp)

    async def _persist_changes(self, doc_id: UUID) -> None:
        """Persist changes to storage.

        Args:
            doc_id: Document ID to persist changes for
        """
        key = f"changes:{doc_id}"
        data = {"changes": [c.to_dict() for c in self._changes[doc_id]]}
        await self.storage.save(key, data)
