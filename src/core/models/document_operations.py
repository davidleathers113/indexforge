"""Document operations models.

This module defines specialized models for document operations service.
Extends core document models with operation-specific functionality.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .documents import DocumentMetadata
from .types import DocumentStatus


class OperationMetadata(BaseModel):
    """Operation-specific metadata."""

    type: str = Field(default="", description="Type of operation performed")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the operation was performed"
    )
    author: str = Field(default="", description="Who performed the operation")
    status: DocumentStatus = Field(
        default=DocumentStatus.PENDING, description="Status of the operation"
    )
    details: dict[str, str] = Field(
        default_factory=dict, description="Additional operation details"
    )


class DocumentOperationMetadata(DocumentMetadata):
    """Document metadata with operation tracking.

    Extends the core DocumentMetadata with operation history tracking.
    """

    operation_history: list[OperationMetadata] = Field(
        default_factory=list, description="History of operations performed on the document"
    )


class OperationResult(BaseModel):
    """Result of a document operation."""

    document_id: UUID = Field(description="ID of the document operated on")
    type: str = Field(description="Type of operation performed")
    success: bool = Field(description="Whether the operation succeeded")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the operation completed"
    )
    error: str | None = Field(default=None, description="Error message if operation failed")
    details: dict[str, str] = Field(
        default_factory=dict, description="Additional operation details"
    )


class BatchOperation(BaseModel):
    """Batch operation request."""

    document_ids: list[UUID] = Field(description="List of document IDs to operate on")
    type: str = Field(description="Type of operation to perform")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Additional metadata for the operation"
    )
    options: dict[str, str] = Field(default_factory=dict, description="Operation-specific options")
