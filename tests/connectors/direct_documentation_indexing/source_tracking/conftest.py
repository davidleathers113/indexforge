"""Shared fixtures for document lineage testing."""

from datetime import datetime, timezone
from typing import Any, Dict

import pytest

from src.connectors.direct_documentation_indexing.source_tracking import (
    add_processing_step,
    log_error_or_warning,
)
from src.connectors.direct_documentation_indexing.source_tracking.alert_manager import AlertConfig
from src.connectors.direct_documentation_indexing.source_tracking.document_operations import (
    add_document,
)
from src.connectors.direct_documentation_indexing.source_tracking.enums import (
    LogLevel,
    ProcessingStatus,
)
from src.connectors.direct_documentation_indexing.source_tracking.storage import LineageStorage


@pytest.fixture
def temp_lineage_dir(tmp_path):
    """Create a temporary directory for test lineage data."""
    return tmp_path / "lineage"


@pytest.fixture
def storage(temp_lineage_dir):
    """Create a LineageStorage instance."""
    return LineageStorage(str(temp_lineage_dir))


@pytest.fixture
def sample_document(storage) -> Dict[str, Any]:
    """Create a sample document with basic metadata."""
    doc_id = "test_doc"
    metadata = {"type": "pdf", "pages": 10, "created_at": datetime.now(timezone.utc).isoformat()}
    add_document(storage, doc_id=doc_id, metadata=metadata)
    return {"id": doc_id, "metadata": metadata}


@pytest.fixture
def processed_document(storage, sample_document) -> Dict[str, Any]:
    """Create a sample document that has been processed successfully."""
    doc_id = sample_document["id"]
    add_processing_step(
        storage,
        doc_id=doc_id,
        step_name="extraction",
        status=ProcessingStatus.SUCCESS,
        details={"chars": 1000},
    )
    return sample_document


@pytest.fixture
def test_alert_config() -> AlertConfig:
    """Create a test alert configuration with standard thresholds."""
    return AlertConfig(
        error_rate_threshold=0.2,
        warning_rate_threshold=0.1,
        memory_critical_threshold=95.0,
        memory_warning_threshold=85.0,
        cpu_critical_threshold=90.0,
        cpu_warning_threshold=80.0,
        disk_critical_threshold=90.0,
        disk_warning_threshold=80.0,
        processing_time_critical=300.0,
        processing_time_warning=150.0,
        alert_cooldown=60,
        email_config={
            "smtp_host": "smtp.test.com",
            "smtp_port": "587",
            "from_address": "test@example.com",
            "to_address": "admin@example.com",
        },
        webhook_urls={
            "slack": "https://hooks.slack.com/test",
            "custom": "https://api.custom.com/webhook",
        },
    )
