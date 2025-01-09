"""
Document lineage tracking system for managing document transformations and relationships.

This package provides a comprehensive system for tracking the lifecycle, transformations,
and relationships of documents in a processing pipeline. It offers robust functionality
for monitoring document processing, managing errors, collecting metrics, and ensuring
system health.

Key Components:
    - DocumentLineageManager: Main interface for document tracking
    - LineageStorage: Persistent storage for lineage data
    - AlertManager: System alerts and notifications
    - CrossReferenceManager: Document relationship tracking
    - HealthCheck: System health monitoring
    - MetricsManager: Performance metrics collection
    - ValidationManager: Data integrity validation

Features:
    - Document lifecycle tracking
    - Processing step management
    - Error and warning logging
    - Performance metrics collection
    - Health monitoring
    - Cross-reference management
    - Multi-tenant support
    - Version history tracking

Example Usage:
    ```python
    from src.connectors.direct_documentation_indexing.source_tracking import (
        DocumentLineageManager,
        ProcessingStatus,
        LogLevel,
    )

    # Initialize the manager
    manager = DocumentLineageManager("/path/to/storage")

    # Add a document
    manager.add_document(
        doc_id="doc123",
        metadata={"type": "pdf", "pages": 10}
    )

    # Track processing
    manager.add_processing_step(
        doc_id="doc123",
        step_name="text_extraction",
        status=ProcessingStatus.SUCCESS,
        details={"chars": 5000}
    )

    # Log issues
    manager.log_error_or_warning(
        doc_id="doc123",
        log_level=LogLevel.WARNING,
        message="Low image quality"
    )

    # Monitor health
    health = manager.health_check()
    print(f"System status: {health.status}")
    ```

For more information, see the README.md file in this directory.
"""

from src.cross_reference import ChunkReference, CrossReferenceManager, ReferenceType

from .alert_manager import Alert, AlertConfig, AlertManager, AlertSeverity, AlertType
from .document_lineage import DocumentLineageManager
from .document_operations import add_document
from .enums import HealthStatus, LogLevel, ProcessingStatus, TransformationType
from .health_check import calculate_health_status
from .lineage_operations import add_derivation, get_derivation_chain
from .logging_manager import (
    add_processing_step,
    get_error_logs,
    get_log_entries,
    get_processing_steps,
    get_recent_errors,
    log_error_or_warning,
)
from .metrics import get_aggregated_metrics, get_real_time_status
from .models import DocumentLineage, HealthCheckResult, LogEntry, ProcessingStep, Transformation
from .reliability import ReliabilityMetrics, SourceReliability
from .source_tracker import SourceConfig, SourceTracker
from .status_manager import count_active_processes
from .storage import LineageStorage, LineageStorageBase
from .storage_manager import get_storage_usage
from .tenant_source_tracker import TenantConfig, TenantSourceTracker
from .utils import format_iso_datetime, load_json, parse_iso_datetime, save_json
from .validation import (
    validate_chunk_references,
    validate_circular_derivations,
    validate_lineage_relationships,
)
from .version_history import Change, ChangeType, VersionHistory, VersionTag

__all__ = [
    # Core Classes
    "DocumentLineageManager",
    "LineageStorage",
    "LineageStorageBase",
    "DocumentLineage",
    # Core Operations
    "add_document",
    "add_derivation",
    "get_derivation_chain",
    # Processing and Logging
    "add_processing_step",
    "log_error_or_warning",
    "get_processing_steps",
    "get_error_logs",
    "get_log_entries",
    "get_recent_errors",
    # Metrics and Status
    "get_aggregated_metrics",
    "get_real_time_status",
    "count_active_processes",
    # Validation
    "validate_lineage_relationships",
    "validate_chunk_references",
    "validate_circular_derivations",
    # Alert Management
    "Alert",
    "AlertConfig",
    "AlertManager",
    "AlertSeverity",
    "AlertType",
    # Cross References
    "CrossReferenceManager",
    "ChunkReference",
    "ReferenceType",
    # Health Check
    "calculate_health_status",
    "HealthCheckResult",
    "HealthStatus",
    # Models and Types
    "LogEntry",
    "ProcessingStep",
    "Transformation",
    # Enums
    "LogLevel",
    "ProcessingStatus",
    "TransformationType",
    "ChangeType",
    # Source and Tenant Management
    "SourceConfig",
    "SourceTracker",
    "TenantConfig",
    "TenantSourceTracker",
    "ReliabilityMetrics",
    "SourceReliability",
    # Version History
    "Change",
    "VersionHistory",
    "VersionTag",
    # Utilities
    "format_iso_datetime",
    "get_storage_usage",
    "load_json",
    "parse_iso_datetime",
    "save_json",
]
