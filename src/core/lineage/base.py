"""Document lineage tracking for IndexForge.

This module provides the core functionality for tracking document lineage,
including source tracking, version history, and relationship management.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    """Type of change made to a document."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    PROCESSED = "processed"
    REFERENCED = "referenced"
    DEREFERENCED = "dereferenced"


class SourceInfo(BaseModel):
    """Information about a document's source."""

    source_id: str = Field(..., description="Unique identifier for the source")
    source_type: str = Field(..., description="Type of source (e.g., git, filesystem, api)")
    location: str = Field(..., description="Location within the source")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Source-specific metadata")


class ChangeRecord(BaseModel):
    """Record of a change made to a document."""

    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the change occurred"
    )
    change_type: ChangeType = Field(..., description="Type of change")
    document_id: UUID = Field(..., description="ID of the document that changed")
    version: int = Field(..., description="Document version after the change")
    source_info: Optional[SourceInfo] = Field(None, description="Source information if relevant")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Change-specific metadata")
    parent_id: Optional[UUID] = Field(None, description="ID of parent document if derived")
    related_ids: Set[UUID] = Field(default_factory=set, description="IDs of related documents")


class DocumentLineage(BaseModel):
    """Complete lineage information for a document."""

    document_id: UUID = Field(..., description="Document ID")
    current_version: int = Field(default=1, description="Current document version")
    source_info: Optional[SourceInfo] = Field(None, description="Current source information")
    parent_id: Optional[UUID] = Field(None, description="ID of parent document if derived")
    children_ids: Set[UUID] = Field(default_factory=set, description="IDs of child documents")
    reference_ids: Set[UUID] = Field(default_factory=set, description="IDs of referenced documents")
    referenced_by_ids: Set[UUID] = Field(
        default_factory=set, description="IDs of documents referencing this one"
    )
    history: List[ChangeRecord] = Field(
        default_factory=list, description="Chronological history of changes"
    )
    metadata: Dict[str, str] = Field(default_factory=dict, description="Current document metadata")

    def add_change(
        self,
        change_type: ChangeType,
        source_info: Optional[SourceInfo] = None,
        metadata: Optional[Dict[str, str]] = None,
        parent_id: Optional[UUID] = None,
        related_ids: Optional[Set[UUID]] = None,
    ) -> None:
        """Add a change record to the document's history.

        Args:
            change_type: Type of change that occurred
            source_info: Optional source information for the change
            metadata: Optional metadata about the change
            parent_id: Optional ID of parent document
            related_ids: Optional set of related document IDs
        """
        self.current_version += 1

        if source_info:
            self.source_info = source_info

        if metadata:
            self.metadata.update(metadata)

        if parent_id:
            self.parent_id = parent_id

        if related_ids:
            if change_type == ChangeType.REFERENCED:
                self.reference_ids.update(related_ids)
            elif change_type == ChangeType.DEREFERENCED:
                self.reference_ids.difference_update(related_ids)

        self.history.append(
            ChangeRecord(
                change_type=change_type,
                document_id=self.document_id,
                version=self.current_version,
                source_info=source_info,
                metadata=metadata or {},
                parent_id=parent_id,
                related_ids=related_ids or set(),
            )
        )

    def get_changes_since(self, version: int) -> List[ChangeRecord]:
        """Get all changes since a specific version.

        Args:
            version: Version number to get changes since

        Returns:
            List of change records since the specified version
        """
        return [change for change in self.history if change.version > version]

    def get_related_documents(self) -> Set[UUID]:
        """Get all documents related to this one.

        This includes parent, children, references, and documents referencing this one.

        Returns:
            Set of related document IDs
        """
        related = set()
        if self.parent_id:
            related.add(self.parent_id)
        related.update(self.children_ids)
        related.update(self.reference_ids)
        related.update(self.referenced_by_ids)
        return related
