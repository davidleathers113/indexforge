"""Tests for document transformation tracking."""

import pytest

from src.connectors.direct_documentation_indexing.source_tracking import add_document
from src.connectors.direct_documentation_indexing.source_tracking.storage import LineageStorage
from src.connectors.direct_documentation_indexing.source_tracking.transformation_manager import (
    get_transformation_history,
    record_transformation,
)
from src.core.tracking.transformations import TransformationType


@pytest.fixture
def temp_lineage_dir(tmp_path):
    """Create a temporary directory for test lineage data."""
    return tmp_path / "lineage"


@pytest.fixture
def storage(temp_lineage_dir):
    """Create a LineageStorage instance."""
    return LineageStorage(str(temp_lineage_dir))


def test_record_transformation(storage):
    """Test recording a document transformation."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)
    transform_type = TransformationType.TEXT_EXTRACTION
    description = "Extract text from PDF"
    parameters = {"engine": "tesseract"}
    record_transformation(
        storage,
        doc_id=doc_id,
        transform_type=transform_type,
        description=description,
        parameters=parameters,
    )
    lineage = storage.get_lineage(doc_id)
    history = get_transformation_history(lineage, transform_type)
    assert len(history) == 1
    assert history[0].transform_type == transform_type
    assert history[0].description == description
    assert history[0].parameters == parameters


def test_get_transformation_history(storage):
    """Test getting transformation history for a document."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)
    transformations = [
        (TransformationType.TEXT_EXTRACTION, "Extract text"),
        (TransformationType.CONTENT_ENRICHMENT, "Enrich content"),
        (TransformationType.METADATA_UPDATE, "Update metadata"),
    ]
    for transform_type, description in transformations:
        record_transformation(
            storage, doc_id=doc_id, transform_type=transform_type, description=description
        )
    lineage = storage.get_lineage(doc_id)
    history = get_transformation_history(lineage)
    assert len(history) == len(transformations)
    filtered = get_transformation_history(lineage, TransformationType.TEXT_EXTRACTION)
    assert len(filtered) == 1
    assert filtered[0].transform_type == TransformationType.TEXT_EXTRACTION


def test_transformation_persistence(temp_lineage_dir):
    """Test persistence of document transformations."""
    storage1 = LineageStorage(str(temp_lineage_dir))
    doc_id = "test_doc"
    add_document(storage1, doc_id=doc_id)
    record_transformation(
        storage1, doc_id=doc_id, transform_type=TransformationType.SPLIT, metadata={"chunks": 3}
    )
    storage2 = LineageStorage(str(temp_lineage_dir))
    lineage = storage2.get_lineage(doc_id)
    if not lineage:
        raise ValueError(f"Document {doc_id} not found in storage2")
    history = get_transformation_history(lineage)
    assert len(history) == 1
    assert history[0].transform_type == TransformationType.SPLIT
    assert history[0].metadata == {"chunks": 3}


def test_transformation_error_handling(storage):
    """Test error handling in transformation operations."""
    doc_id = "test_doc"
    add_document(storage, doc_id=doc_id)
    with pytest.raises(ValueError):
        record_transformation(storage, doc_id=doc_id, transform_type="invalid_type")
    with pytest.raises(ValueError):
        record_transformation(
            storage, doc_id="non_existent", transform_type=TransformationType.TEXT_EXTRACTION
        )
