"""Tests for JSON storage implementation."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel

from src.core.storage.strategies.base import DataCorruptionError, DataNotFoundError
from src.core.storage.strategies.json_storage import JsonSerializationError, JsonStorage


class TestModel(BaseModel):
    """Test model for storage."""

    id: UUID
    name: str
    created_at: datetime
    metadata: dict


@pytest.fixture
def test_data() -> TestModel:
    """Create test data."""
    return TestModel(
        id=uuid4(),
        name="test",
        created_at=datetime.now(UTC),
        metadata={"key": "value"},
    )


@pytest.fixture
def storage(tmp_path: Path) -> JsonStorage[TestModel]:
    """Create test storage."""
    return JsonStorage(tmp_path / "test", TestModel)


def test_save_and_load(storage: JsonStorage[TestModel], test_data: TestModel) -> None:
    """Test saving and loading data."""
    # Save data
    storage.save(str(test_data.id), test_data)

    # Load data
    loaded = storage.load(str(test_data.id))

    # Verify
    assert loaded.id == test_data.id
    assert loaded.name == test_data.name
    assert loaded.created_at == test_data.created_at
    assert loaded.metadata == test_data.metadata


def test_load_nonexistent(storage: JsonStorage[TestModel]) -> None:
    """Test loading nonexistent data."""
    with pytest.raises(DataNotFoundError):
        storage.load("nonexistent")


def test_delete(storage: JsonStorage[TestModel], test_data: TestModel) -> None:
    """Test deleting data."""
    # Save data
    key = str(test_data.id)
    storage.save(key, test_data)

    # Verify exists
    assert storage.exists(key)

    # Delete
    storage.delete(key)

    # Verify gone
    assert not storage.exists(key)


def test_delete_nonexistent(storage: JsonStorage[TestModel]) -> None:
    """Test deleting nonexistent data."""
    with pytest.raises(DataNotFoundError):
        storage.delete("nonexistent")


def test_exists(storage: JsonStorage[TestModel], test_data: TestModel) -> None:
    """Test exists check."""
    key = str(test_data.id)
    assert not storage.exists(key)

    storage.save(key, test_data)
    assert storage.exists(key)


def test_invalid_json(storage: JsonStorage[TestModel], test_data: TestModel) -> None:
    """Test handling invalid JSON data."""
    # Save corrupted data
    key = str(test_data.id)
    path = storage._get_path(key)
    path.write_text("invalid json")

    with pytest.raises(DataCorruptionError):
        storage.load(key)


def test_invalid_model_data(storage: JsonStorage[TestModel]) -> None:
    """Test handling invalid model data."""
    # Save data missing required fields
    key = "test"
    path = storage._get_path(key)
    path.write_text('{"name": "test"}')

    with pytest.raises(JsonSerializationError):
        storage.load(key)


def test_safe_key_generation(storage: JsonStorage[TestModel], test_data: TestModel) -> None:
    """Test safe key generation."""
    key = "test/with/slashes and spaces"
    storage.save(key, test_data)

    safe_path = storage._get_path(key)
    assert safe_path.name == "test_with_slashes_and_spaces.json"
    assert storage.exists(key)
