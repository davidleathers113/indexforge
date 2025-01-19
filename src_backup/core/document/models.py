"""Document models and data structures.

This module defines the core document models and their relationships.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Document metadata information."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    author: str = Field(default="")
    version: str = Field(default="1.0.0")
    tags: list[str] = Field(default_factory=list)
    properties: dict[str, str] = Field(default_factory=dict)


class DocumentRelationship(BaseModel):
    """Document relationship information."""

    source_id: UUID
    target_id: UUID
    relationship_type: str = Field(default="reference")
    properties: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Document(BaseModel):
    """Core document model."""

    id: UUID
    content: str
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    relationships: list[DocumentRelationship] = Field(default_factory=list)
    parent_id: UUID | None = None
    is_active: bool = Field(default=True)
    last_processed: datetime | None = None
