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
from .enums import HealthStatus, LogLevel, ProcessingStatus, TransformationType
from .error_logging import log_error_or_warning
from .health_check import calculate_health_status
from .lineage.manager import DocumentLineageManager
from .lineage.operations import add_derivation, get_derivation_chain, validate_lineage_relationships
from .metrics import get_aggregated_metrics, get_real_time_status
from .models.health import HealthCheckResult
from .models.lineage import DocumentLineage
from .models.logging import LogEntry
from .models.processing import ProcessingStep
from .models.transformation import Transformation
from .operations import add_document
from .source.config import SourceConfig
from .source.tracker import SourceTracker
from .status_manager import count_active_processes
from .storage import LineageStorage, LineageStorageBase
from .storage_manager import get_storage_usage
from .transformations import (
    DocumentNotFoundError,
    InvalidTransformationError,
    TransformationError,
    TransformationManager,
)
from .utils import format_iso_datetime, load_json, parse_iso_datetime, save_json
from .validation.strategies.circular import validate_no_circular_reference
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
    "log_error_or_warning",
    # Metrics and Status
    "get_aggregated_metrics",
    "get_real_time_status",
    "count_active_processes",
    # Validation
    "validate_lineage_relationships",
    "validate_no_circular_reference",
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
    # Source Management
    "SourceConfig",
    "SourceTracker",
    # Version History
    "Change",
    "VersionHistory",
    "VersionTag",
    # Transformation Management
    "TransformationManager",
    "TransformationError",
    "DocumentNotFoundError",
    "InvalidTransformationError",
    # Utilities
    "format_iso_datetime",
    "get_storage_usage",
    "load_json",
    "parse_iso_datetime",
    "save_json",
]
