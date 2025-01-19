"""Integration tests for document lineage functionality."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from src.core.tracking.lineage.manager import DocumentLineageManager
from src.core.tracking.lineage.operations import add_derivation
from src.core.tracking.models.transformation import TransformationType
from src.core.tracking.operations import add_document


@pytest.fixture
def storage_dir(tmp_path) -> Path:
    """Create a temporary storage directory."""
    storage_path = tmp_path / "test_storage"
    storage_path.mkdir()
    return storage_path


@pytest.fixture
def manager(storage_dir) -> DocumentLineageManager:
    """Create a DocumentLineageManager instance."""
    return DocumentLineageManager(str(storage_dir))


@pytest.fixture
def sample_metadata() -> dict:
    """Create sample document metadata."""
    return {
        "type": "pdf",
        "pages": 10,
        "created_at": datetime.now(UTC).isoformat(),
        "source": "test",
        "version": "1.0",
    }


@pytest.fixture
def transformation_chain(manager: DocumentLineageManager, sample_metadata: dict) -> list[str]:
    """Create a chain of documents with various transformations."""
    doc_ids = []
    transform_types = [
        TransformationType.CONVERSION,
        TransformationType.EXTRACTION,
        TransformationType.UPDATE,
    ]

    # Create initial document
    doc_id = "original_doc"
    add_document(manager.storage, doc_id=doc_id, metadata=sample_metadata)
    doc_ids.append(doc_id)

    # Create chain of transformations
    for i, transform_type in enumerate(transform_types, 1):
        derived_id = f"derived_doc_{i}"
        derived_metadata = sample_metadata.copy()
        derived_metadata.update(
            {
                "version": f"1.{i}",
                "transformation": transform_type,
            }
        )

        # Add document
        add_document(
            manager.storage,
            doc_id=derived_id,
            parent_ids=[doc_ids[-1]],
            metadata=derived_metadata,
        )

        # Add derivation with transformation
        add_derivation(
            manager.storage,
            parent_id=doc_ids[-1],
            derived_id=derived_id,
            transform_type=transform_type,
            description=f"Applied {transform_type} transformation",
            parameters={"quality": "high"},
            metadata={"processor_version": "1.0"},
        )

        doc_ids.append(derived_id)

    return doc_ids


def test_transformation_history_tracking(
    manager: DocumentLineageManager,
    transformation_chain: list[str],
):
    """Test tracking and retrieval of transformation history."""
    # Get history for last document
    doc_id = transformation_chain[-1]
    history = manager.get_transformation_history(doc_id)

    # Verify transformations
    assert len(history) > 0
    for transform in history:
        assert transform.type in [
            TransformationType.CONVERSION,
            TransformationType.EXTRACTION,
            TransformationType.UPDATE,
        ]
        assert transform.parameters == {"quality": "high"}
        assert transform.metadata == {"processor_version": "1.0"}


def test_filtered_transformation_history(
    manager: DocumentLineageManager,
    transformation_chain: list[str],
):
    """Test filtering of transformation history."""
    doc_id = transformation_chain[-1]

    # Filter by type
    conversion_history = manager.get_transformation_history(
        doc_id,
        transform_type=TransformationType.CONVERSION,
    )
    assert all(t.type == TransformationType.CONVERSION for t in conversion_history)

    # Filter by time range
    now = datetime.now(UTC)
    recent_history = manager.get_transformation_history(
        doc_id,
        start_time=now - timedelta(minutes=5),
        end_time=now,
    )
    assert all(
        now - timedelta(minutes=5) <= datetime.fromisoformat(t.timestamp) <= now
        for t in recent_history
    )


def test_transformation_persistence(
    manager: DocumentLineageManager,
    transformation_chain: list[str],
    storage_dir: Path,
):
    """Test persistence of transformation history across manager instances."""
    doc_id = transformation_chain[-1]
    original_history = manager.get_transformation_history(doc_id)

    # Create new manager instance
    new_manager = DocumentLineageManager(str(storage_dir))
    new_history = new_manager.get_transformation_history(doc_id)

    # Compare histories
    assert len(original_history) == len(new_history)
    for orig, new in zip(original_history, new_history, strict=False):
        assert orig.type == new.type
        assert orig.description == new.description
        assert orig.parameters == new.parameters
        assert orig.metadata == new.metadata


def test_complex_transformation_graph(
    manager: DocumentLineageManager,
    sample_metadata: dict,
):
    """Test handling of complex transformation graphs."""
    # Create documents with multiple transformation paths
    doc_ids = {
        "original": "original_doc",
        "text": "text_doc",
        "summary": "summary_doc",
        "translated": "translated_doc",
        "final": "final_doc",
    }

    # Create original document
    add_document(manager.storage, doc_id=doc_ids["original"], metadata=sample_metadata)

    # Create text conversion
    add_document(
        manager.storage,
        doc_id=doc_ids["text"],
        parent_ids=[doc_ids["original"]],
        metadata={"type": "text", **sample_metadata},
    )
    add_derivation(
        manager.storage,
        parent_id=doc_ids["original"],
        derived_id=doc_ids["text"],
        transform_type=TransformationType.CONVERSION,
        description="PDF to text conversion",
    )

    # Create summary from text
    add_document(
        manager.storage,
        doc_id=doc_ids["summary"],
        parent_ids=[doc_ids["text"]],
        metadata={"type": "summary", **sample_metadata},
    )
    add_derivation(
        manager.storage,
        parent_id=doc_ids["text"],
        derived_id=doc_ids["summary"],
        transform_type=TransformationType.EXTRACTION,
        description="Text summarization",
    )

    # Create translation from text
    add_document(
        manager.storage,
        doc_id=doc_ids["translated"],
        parent_ids=[doc_ids["text"]],
        metadata={"type": "translation", **sample_metadata},
    )
    add_derivation(
        manager.storage,
        parent_id=doc_ids["text"],
        derived_id=doc_ids["translated"],
        transform_type=TransformationType.CONVERSION,
        description="Text translation",
    )

    # Create final document from both summary and translation
    add_document(
        manager.storage,
        doc_id=doc_ids["final"],
        parent_ids=[doc_ids["summary"], doc_ids["translated"]],
        metadata={"type": "final", **sample_metadata},
    )
    for parent_id in [doc_ids["summary"], doc_ids["translated"]]:
        add_derivation(
            manager.storage,
            parent_id=parent_id,
            derived_id=doc_ids["final"],
            transform_type=TransformationType.MERGE,
            description="Merge summary and translation",
        )

    # Verify transformation histories
    final_history = manager.get_transformation_history(doc_ids["final"])
    assert len(final_history) >= 2  # Should have at least merge transformations

    # Verify specific transformation types
    conversion_history = manager.get_transformation_history(
        doc_ids["final"],
        transform_type=TransformationType.CONVERSION,
    )
    assert len(conversion_history) > 0

    extraction_history = manager.get_transformation_history(
        doc_ids["final"],
        transform_type=TransformationType.EXTRACTION,
    )
    assert len(extraction_history) > 0

    merge_history = manager.get_transformation_history(
        doc_ids["final"],
        transform_type=TransformationType.MERGE,
    )
    assert len(merge_history) > 0


def test_concurrent_transformation_tracking(
    manager: DocumentLineageManager,
    sample_metadata: dict,
):
    """Test handling of concurrent transformation operations."""
    doc_id = "concurrent_doc"
    derived_id = "derived_doc"

    # Create original document
    add_document(manager.storage, doc_id=doc_id, metadata=sample_metadata)

    # Create derived document
    add_document(
        manager.storage,
        doc_id=derived_id,
        parent_ids=[doc_id],
        metadata=sample_metadata,
    )

    # Add multiple transformations concurrently
    transform_types = [
        TransformationType.CONVERSION,
        TransformationType.EXTRACTION,
        TransformationType.UPDATE,
    ]

    for transform_type in transform_types:
        add_derivation(
            manager.storage,
            parent_id=doc_id,
            derived_id=derived_id,
            transform_type=transform_type,
            description=f"Concurrent {transform_type}",
        )

    # Verify all transformations were recorded
    history = manager.get_transformation_history(derived_id)
    recorded_types = {t.type for t in history}
    assert recorded_types == set(transform_types)
