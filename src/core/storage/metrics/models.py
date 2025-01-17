"""Storage metrics models.

This module defines the data models for storage metrics collection,
including operation metrics and system resource usage.

Key Features:
    - Operation metrics (create, update, delete)
    - Storage usage metrics (disk space, file counts)
    - Performance metrics (latency, throughput)
    - Type-safe metric models
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class OperationMetrics(BaseModel):
    """Metrics for storage operations."""

    operation_type: str = Field(..., description="Type of operation (create/update/delete)")
    document_id: str = Field(..., description="ID of document involved")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_ms: float = Field(..., description="Operation duration in milliseconds")
    success: bool = Field(..., description="Whether operation succeeded")
    error_message: str | None = Field(None, description="Error message if operation failed")


class StorageMetrics(BaseModel):
    """Metrics for storage system."""

    total_space_bytes: int = Field(..., description="Total storage space in bytes")
    used_space_bytes: int = Field(..., description="Used storage space in bytes")
    free_space_bytes: int = Field(..., description="Free storage space in bytes")
    total_documents: int = Field(..., description="Total number of documents")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PerformanceMetrics(BaseModel):
    """Performance metrics for storage operations."""

    avg_latency_ms: float = Field(..., description="Average operation latency in milliseconds")
    throughput_ops: float = Field(..., description="Operations per second")
    error_rate: float = Field(..., description="Error rate as fraction")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    window_seconds: int = Field(..., description="Time window for metrics in seconds")
