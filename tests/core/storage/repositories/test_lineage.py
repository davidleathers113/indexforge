"""Tests for lineage repository implementation."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from src.core.models.lineage import DocumentLineage
from src.core.storage.repositories.base import DocumentExistsError, DocumentNotFoundError
from src.core.storage.repositories.lineage import LineageRepository


@pytest.fixture
def test_lineage() -> DocumentLineage:
    """Create a test document lineage."""
    doc_id = uuid4()
    return DocumentLineage(
        doc_id=doc_id,
        origin_id=uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        transformations=[],
        processing_steps=[],
    )


@pytest.fixture
def repository(tmp_path: Path) -> LineageRepository:
    """Create a test repository."""
    return LineageRepository(tmp_path / "lineage")


def test_create_and_get(repository: LineageRepository, test_lineage: DocumentLineage) -> None:
    """Test creating and retrieving lineage."""
    # Create lineage
    repository.create(test_lineage)

    # Get lineage
    retrieved = repository.get(test_lineage.doc_id)

    # Verify
    assert retrieved.doc_id == test_lineage.doc_id
    assert retrieved.origin_id == test_lineage.origin_id
    assert retrieved.transformations == test_lineage.transformations
    assert retrieved.processing_steps == test_lineage.processing_steps


def test_create_duplicate(repository: LineageRepository, test_lineage: DocumentLineage) -> None:
    """Test creating duplicate lineage."""
    repository.create(test_lineage)

    with pytest.raises(DocumentExistsError):
        repository.create(test_lineage)


def test_update(repository: LineageRepository, test_lineage: DocumentLineage) -> None:
    """Test updating lineage."""
    # Create lineage
    repository.create(test_lineage)

    # Update lineage
    test_lineage.transformations = ["transform1", "transform2"]
    test_lineage.processing_steps = ["step1", "step2"]
    repository.update(test_lineage)

    # Verify
    updated = repository.get(test_lineage.doc_id)
    assert updated.transformations == ["transform1", "transform2"]
    assert updated.processing_steps == ["step1", "step2"]


def test_update_nonexistent(repository: LineageRepository, test_lineage: DocumentLineage) -> None:
    """Test updating nonexistent lineage."""
    with pytest.raises(DocumentNotFoundError):
        repository.update(test_lineage)


def test_delete(repository: LineageRepository, test_lineage: DocumentLineage) -> None:
    """Test deleting lineage."""
    # Create lineage
    repository.create(test_lineage)

    # Verify exists
    assert repository.exists(test_lineage.doc_id)

    # Delete
    repository.delete(test_lineage.doc_id)

    # Verify gone
    assert not repository.exists(test_lineage.doc_id)


def test_delete_nonexistent(repository: LineageRepository) -> None:
    """Test deleting nonexistent lineage."""
    with pytest.raises(DocumentNotFoundError):
        repository.delete(uuid4())


def test_exists(repository: LineageRepository, test_lineage: DocumentLineage) -> None:
    """Test exists check."""
    assert not repository.exists(test_lineage.doc_id)

    repository.create(test_lineage)
    assert repository.exists(test_lineage.doc_id)


def test_list_ids(repository: LineageRepository) -> None:
    """Test listing lineage IDs."""
    # Create some lineage records
    lineages = [
        DocumentLineage(
            doc_id=uuid4(),
            origin_id=uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            transformations=[f"transform{i}"],
            processing_steps=[f"step{i}"],
        )
        for i in range(3)
    ]

    for lineage in lineages:
        repository.create(lineage)

    # Get IDs
    ids = repository.list_ids()

    # Verify
    assert len(ids) == 3
    assert all(lineage.doc_id in ids for lineage in lineages)


def test_get_by_origin(repository: LineageRepository) -> None:
    """Test getting lineage by origin."""
    # Create lineage records with same origin
    origin_id = uuid4()
    lineages = [
        DocumentLineage(
            doc_id=uuid4(),
            origin_id=origin_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            transformations=[f"transform{i}"],
            processing_steps=[f"step{i}"],
        )
        for i in range(3)
    ]

    # Add one with different origin
    different_origin = DocumentLineage(
        doc_id=uuid4(),
        origin_id=uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        transformations=["other"],
        processing_steps=["other"],
    )
    lineages.append(different_origin)

    for lineage in lineages:
        repository.create(lineage)

    # Get by origin
    results = repository.get_by_origin(origin_id)

    # Verify
    assert len(results) == 3
    assert all(lineage.origin_id == origin_id for lineage in results)


def test_get_by_time_range(repository: LineageRepository) -> None:
    """Test getting lineage by time range."""
    now = datetime.now(UTC)

    # Create lineage records at different times
    lineages = [
        DocumentLineage(
            doc_id=uuid4(),
            origin_id=uuid4(),
            created_at=now - timedelta(hours=i),
            updated_at=now,
            transformations=[f"transform{i}"],
            processing_steps=[f"step{i}"],
        )
        for i in range(5)
    ]

    for lineage in lineages:
        repository.create(lineage)

    # Get by time range
    start_time = now - timedelta(hours=3)
    end_time = now - timedelta(hours=1)
    results = repository.get_by_time_range(start_time, end_time)

    # Verify
    assert len(results) == 2
    assert all(start_time <= lineage.created_at <= end_time for lineage in results)


def test_get_by_time_range_no_start(repository: LineageRepository) -> None:
    """Test getting lineage by time range with no start time."""
    now = datetime.now(UTC)

    # Create lineage records
    lineages = [
        DocumentLineage(
            doc_id=uuid4(),
            origin_id=uuid4(),
            created_at=now - timedelta(hours=i),
            updated_at=now,
            transformations=[f"transform{i}"],
            processing_steps=[f"step{i}"],
        )
        for i in range(3)
    ]

    for lineage in lineages:
        repository.create(lineage)

    # Get by time range with only end time
    end_time = now - timedelta(hours=1)
    results = repository.get_by_time_range(end_time=end_time)

    # Verify
    assert len(results) == 2
    assert all(lineage.created_at <= end_time for lineage in results)


def test_get_by_time_range_no_end(repository: LineageRepository) -> None:
    """Test getting lineage by time range with no end time."""
    now = datetime.now(UTC)

    # Create lineage records
    lineages = [
        DocumentLineage(
            doc_id=uuid4(),
            origin_id=uuid4(),
            created_at=now - timedelta(hours=i),
            updated_at=now,
            transformations=[f"transform{i}"],
            processing_steps=[f"step{i}"],
        )
        for i in range(3)
    ]

    for lineage in lineages:
        repository.create(lineage)

    # Get by time range with only start time
    start_time = now - timedelta(hours=1)
    results = repository.get_by_time_range(start_time=start_time)

    # Verify
    assert len(results) == 2
    assert all(lineage.created_at >= start_time for lineage in results)
