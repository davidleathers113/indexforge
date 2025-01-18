"""Tests for version history management."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from src.core.lineage.version.manager import VersionManager
from src.core.lineage.version.types import VersionChangeType, VersionTagError


@pytest.fixture
def storage(mocker):
    """Mock storage strategy."""
    return mocker.Mock()


@pytest.fixture
def version_manager(storage):
    """Version manager instance for testing."""
    return VersionManager(storage)


@pytest.fixture
def doc_id():
    """Sample document ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.mark.asyncio
async def test_create_tag(version_manager, doc_id):
    """Test creating a new version tag."""
    tag = await version_manager.create_tag(
        doc_id=doc_id,
        tag="v1.0.0",
        description="Initial release",
        author="test.user",
        change_type=VersionChangeType.SCHEMA,
        reliability_score=0.95,
    )

    assert tag.tag == "v1.0.0"
    assert tag.description == "Initial release"
    assert tag.author == "test.user"
    assert tag.change_type == VersionChangeType.SCHEMA
    assert tag.reliability_score == 0.95


@pytest.mark.asyncio
async def test_create_duplicate_tag(version_manager, doc_id):
    """Test error when creating duplicate tag."""
    await version_manager.create_tag(
        doc_id=doc_id,
        tag="v1.0.0",
        description="Initial release",
        author="test.user",
        change_type=VersionChangeType.SCHEMA,
    )

    with pytest.raises(VersionTagError) as exc:
        await version_manager.create_tag(
            doc_id=doc_id,
            tag="v1.0.0",
            description="Duplicate tag",
            author="test.user",
            change_type=VersionChangeType.CONFIG,
        )
    assert "already exists" in str(exc.value)


@pytest.mark.asyncio
async def test_get_tags_sorted(version_manager, doc_id):
    """Test retrieving tags in chronological order."""
    # Create tags in reverse chronological order
    await version_manager.create_tag(
        doc_id=doc_id,
        tag="v1.1.0",
        description="Second release",
        author="test.user",
        change_type=VersionChangeType.CONFIG,
    )

    await version_manager.create_tag(
        doc_id=doc_id,
        tag="v1.0.0",
        description="Initial release",
        author="test.user",
        change_type=VersionChangeType.SCHEMA,
    )

    tags = await version_manager.get_tags(doc_id)
    assert len(tags) == 2
    assert [t.tag for t in tags] == ["v1.0.0", "v1.1.0"]


@pytest.mark.asyncio
async def test_storage_integration(version_manager, storage, doc_id):
    """Test storage integration for persistence."""
    storage.load.return_value = {"tags": []}

    await version_manager.create_tag(
        doc_id=doc_id,
        tag="v1.0.0",
        description="Initial release",
        author="test.user",
        change_type=VersionChangeType.SCHEMA,
    )

    storage.save.assert_called_once()
    save_data = storage.save.call_args[0][1]
    assert len(save_data["tags"]) == 1
    assert save_data["tags"][0]["tag"] == "v1.0.0"
