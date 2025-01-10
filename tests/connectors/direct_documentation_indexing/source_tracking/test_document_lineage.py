"""Integration tests for document lineage functionality.

This module serves as an entry point for document lineage testing.
Individual test components have been split into separate modules for better organization:

- test_basic_document_operations.py: Basic document CRUD operations
- test_document_transformations.py: Transformation tracking
- test_document_lineage_relationships.py: Parent-child relationships
- test_document_processing_steps.py: Processing step tracking
- test_document_error_logging.py: Error and warning logging
"""

import pytest

from src.connectors.direct_documentation_indexing.source_tracking.storage import LineageStorage


@pytest.fixture
def temp_lineage_dir(tmp_path):
    """Create a temporary directory for test lineage data."""
    return tmp_path / "lineage"


@pytest.fixture
def storage(temp_lineage_dir):
    """Create a LineageStorage instance."""
    return LineageStorage(str(temp_lineage_dir))


def test_lineage_storage_initialization(temp_lineage_dir):
    """Test basic initialization of LineageStorage."""
    storage = LineageStorage(str(temp_lineage_dir))
    assert storage is not None
    assert storage.base_path == str(temp_lineage_dir)
