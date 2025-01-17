"""Shared fixtures for document tracking tests."""

import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Generator

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture

from src.core.tracking.operations import add_document

from .mocks import MockLineageStorage

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("test_tracking.log", mode="w"),
    ],
)

logger = logging.getLogger(__name__)


def pytest_runtest_setup(item):
    """Set up logging for each test."""
    logger.info("=" * 80)
    logger.info(f"Starting test: {item.name}")
    logger.info("=" * 80)


def pytest_runtest_teardown(item, nextitem):
    """Clean up after each test."""
    logger.info("-" * 80)
    logger.info(f"Finished test: {item.name}")
    logger.info("-" * 80)


@pytest.fixture
def temp_lineage_dir(tmp_path, request: FixtureRequest) -> Path:
    """Create a temporary directory for test lineage data.

    Args:
        tmp_path: Pytest's temporary path fixture
        request: Pytest fixture request object for test information

    Returns:
        Path: Temporary directory for lineage data
    """
    lineage_dir = tmp_path / "lineage"
    logger.info("Creating temporary lineage directory: %s", lineage_dir)
    lineage_dir.mkdir(exist_ok=True)

    def cleanup():
        logger.info("Cleaning up temporary lineage directory: %s", lineage_dir)
        if lineage_dir.exists():
            for file in lineage_dir.glob("*"):
                file.unlink()
            lineage_dir.rmdir()

    request.addfinalizer(cleanup)
    return lineage_dir


@pytest.fixture
def storage(temp_lineage_dir: Path, caplog: LogCaptureFixture) -> MockLineageStorage:
    """Create a LineageStorage instance.

    Args:
        temp_lineage_dir: Temporary directory for lineage data
        caplog: Pytest's log capture fixture

    Returns:
        MockLineageStorage: Configured storage instance
    """
    caplog.set_level(logging.DEBUG)
    logger.info("Initializing LineageStorage with directory: %s", temp_lineage_dir)
    storage = MockLineageStorage(str(temp_lineage_dir))
    return storage


@pytest.fixture
def sample_document(storage: MockLineageStorage, caplog: LogCaptureFixture) -> dict[str, Any]:
    """Create a sample document with basic metadata.

    Args:
        storage: LineageStorage instance
        caplog: Pytest's log capture fixture

    Returns:
        dict: Document data including ID and metadata
    """
    caplog.set_level(logging.DEBUG)
    doc_id = "test_doc"
    metadata = {
        "type": "pdf",
        "pages": 10,
        "created_at": datetime.now(UTC).isoformat(),
        "test_context": "sample_document fixture",
    }

    logger.info("Creating sample document - ID: %s", doc_id)
    logger.debug("Sample document metadata: %s", metadata)

    try:
        add_document(storage, doc_id=doc_id, metadata=metadata)
        logger.info("Successfully created sample document")
    except Exception as e:
        logger.error("Failed to create sample document: %s", str(e))
        raise

    return {"id": doc_id, "metadata": metadata}


@pytest.fixture
def parent_document(storage: MockLineageStorage, caplog: LogCaptureFixture) -> dict[str, Any]:
    """Create a sample parent document.

    Args:
        storage: LineageStorage instance
        caplog: Pytest's log capture fixture

    Returns:
        dict: Parent document data including ID and metadata
    """
    caplog.set_level(logging.DEBUG)
    doc_id = "parent_doc"
    metadata = {
        "type": "word",
        "pages": 5,
        "created_at": datetime.now(UTC).isoformat(),
        "version": "1.0",
        "test_context": "parent_document fixture",
    }

    logger.info("Creating parent document - ID: %s", doc_id)
    logger.debug("Parent document metadata: %s", metadata)

    try:
        add_document(storage, doc_id=doc_id, metadata=metadata)
        logger.info("Successfully created parent document")
    except Exception as e:
        logger.error("Failed to create parent document: %s", str(e))
        raise

    return {"id": doc_id, "metadata": metadata}


@pytest.fixture
def child_document(
    storage: MockLineageStorage,
    parent_document: dict[str, Any],
    caplog: LogCaptureFixture,
) -> dict[str, Any]:
    """Create a sample child document with a parent relationship.

    Args:
        storage: LineageStorage instance
        parent_document: Parent document fixture
        caplog: Pytest's log capture fixture

    Returns:
        dict: Child document data including ID, metadata, and parent ID
    """
    caplog.set_level(logging.DEBUG)
    doc_id = "child_doc"
    metadata = {
        "type": "pdf",
        "pages": 5,
        "created_at": datetime.now(UTC).isoformat(),
        "version": "1.1",
        "test_context": "child_document fixture",
    }

    logger.info(
        "Creating child document - ID: %s, Parent ID: %s",
        doc_id,
        parent_document["id"],
    )
    logger.debug("Child document metadata: %s", metadata)

    try:
        add_document(
            storage,
            doc_id=doc_id,
            metadata=metadata,
            parent_ids=[parent_document["id"]],
        )
        logger.info("Successfully created child document")
    except Exception as e:
        logger.error("Failed to create child document: %s", str(e))
        raise

    return {
        "id": doc_id,
        "metadata": metadata,
        "parent_id": parent_document["id"],
    }


@pytest.fixture(autouse=True)
def setup_test_logging(caplog: LogCaptureFixture) -> Generator[None, None, None]:
    """Configure logging for each test automatically.

    Args:
        caplog: Pytest's log capture fixture

    Yields:
        None
    """
    caplog.set_level(logging.DEBUG)

    # Clear any existing handlers to avoid duplicate logs
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Configure test-specific logging
    log_format = "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
    formatter = logging.Formatter(log_format)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler for the current test
    test_name = os.environ.get("PYTEST_CURRENT_TEST", "unknown_test").split(":")[-1].split(" ")[0]
    file_handler = logging.FileHandler(f"test_tracking_{test_name}.log", mode="w")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    root_logger.setLevel(logging.DEBUG)

    yield

    # Clean up handlers
    root_logger.removeHandler(console_handler)
    root_logger.removeHandler(file_handler)
    file_handler.close()
