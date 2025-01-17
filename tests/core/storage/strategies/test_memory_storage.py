"""Tests for memory storage strategy."""

import threading
from datetime import UTC, datetime
from typing import List
from uuid import uuid4

import pytest
from pydantic import BaseModel, Field

from src.core.storage.strategies.base import DataCorruptionError, DataNotFoundError, StorageError
from src.core.storage.strategies.memory_storage import MemoryStorage


class TestModel(BaseModel):
    """Test model for storage."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Name field")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict = Field(default_factory=dict)


@pytest.fixture
def storage() -> MemoryStorage[TestModel]:
    """Create a test storage instance."""
    return MemoryStorage(TestModel)


@pytest.fixture
def test_data() -> TestModel:
    """Create test data."""
    return TestModel(
        id=str(uuid4()),
        name="test",
        metadata={"key": "value"},
    )


def test_save_and_load(storage: MemoryStorage[TestModel], test_data: TestModel) -> None:
    """Test saving and loading data."""
    # Save data
    storage.save(test_data.id, test_data)

    # Load data
    loaded = storage.load(test_data.id)

    # Verify
    assert loaded.id == test_data.id
    assert loaded.name == test_data.name
    assert loaded.metadata == test_data.metadata


def test_load_nonexistent(storage: MemoryStorage[TestModel]) -> None:
    """Test loading nonexistent data."""
    with pytest.raises(DataNotFoundError):
        storage.load("nonexistent")


def test_save_invalid_type(storage: MemoryStorage[TestModel]) -> None:
    """Test saving invalid type."""
    invalid_data = {"id": "123", "name": "test"}
    with pytest.raises(StorageError):
        storage.save("test", invalid_data)  # type: ignore


def test_delete(storage: MemoryStorage[TestModel], test_data: TestModel) -> None:
    """Test deleting data."""
    # Save data
    storage.save(test_data.id, test_data)
    assert storage.exists(test_data.id)

    # Delete data
    storage.delete(test_data.id)
    assert not storage.exists(test_data.id)

    # Verify load raises error
    with pytest.raises(DataNotFoundError):
        storage.load(test_data.id)


def test_delete_nonexistent(storage: MemoryStorage[TestModel]) -> None:
    """Test deleting nonexistent data."""
    with pytest.raises(DataNotFoundError):
        storage.delete("nonexistent")


def test_exists(storage: MemoryStorage[TestModel], test_data: TestModel) -> None:
    """Test exists check."""
    assert not storage.exists(test_data.id)

    storage.save(test_data.id, test_data)
    assert storage.exists(test_data.id)


def test_clear(storage: MemoryStorage[TestModel], test_data: TestModel) -> None:
    """Test clearing all data."""
    # Save multiple items
    for i in range(3):
        data = TestModel(
            id=str(uuid4()),
            name=f"test{i}",
        )
        storage.save(data.id, data)

    # Clear all data
    storage.clear()

    # Verify all data is gone
    with pytest.raises(DataNotFoundError):
        storage.load(test_data.id)


def test_data_isolation(storage: MemoryStorage[TestModel], test_data: TestModel) -> None:
    """Test data isolation between save/load."""
    # Save data
    storage.save(test_data.id, test_data)

    # Load data and modify it
    loaded = storage.load(test_data.id)
    loaded.name = "modified"
    loaded.metadata["new"] = "value"

    # Load again and verify original is unchanged
    reloaded = storage.load(test_data.id)
    assert reloaded.name == test_data.name
    assert reloaded.metadata == test_data.metadata


def test_simulated_failures() -> None:
    """Test simulated storage failures."""
    storage = MemoryStorage(TestModel, simulate_failures=True)
    data = TestModel(id="fail_test", name="test")

    with pytest.raises(StorageError):
        storage.save("fail_test", data)

    with pytest.raises(StorageError):
        storage.load("fail_test")

    with pytest.raises(StorageError):
        storage.delete("fail_test")


def test_last_modified(storage: MemoryStorage[TestModel], test_data: TestModel) -> None:
    """Test last modified timestamp updates."""
    initial_time = storage.get_last_modified()

    # Save data
    storage.save(test_data.id, test_data)
    save_time = storage.get_last_modified()
    assert save_time > initial_time

    # Delete data
    storage.delete(test_data.id)
    delete_time = storage.get_last_modified()
    assert delete_time > save_time


def test_concurrent_access(storage: MemoryStorage[TestModel]) -> None:
    """Test concurrent access to storage."""
    total_threads = 10
    operations_per_thread = 100
    results: List[Exception] = []

    def worker() -> None:
        """Worker function for concurrent testing."""
        try:
            for _ in range(operations_per_thread):
                # Create unique data
                data = TestModel(id=str(uuid4()), name="test")

                # Perform operations
                storage.save(data.id, data)
                loaded = storage.load(data.id)
                assert loaded.id == data.id
                storage.delete(data.id)
                assert not storage.exists(data.id)
        except Exception as e:
            results.append(e)

    # Start threads
    threads = [threading.Thread(target=worker) for _ in range(total_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Verify no errors occurred
    assert not results, f"Errors during concurrent access: {results}"


def test_data_corruption(storage: MemoryStorage[TestModel], test_data: TestModel) -> None:
    """Test handling of corrupted data."""
    # Save valid data
    storage.save(test_data.id, test_data)

    # Corrupt the data
    with storage._lock:
        storage._data[test_data.id]["name"] = 123  # type: ignore

    # Attempt to load corrupted data
    with pytest.raises(DataCorruptionError):
        storage.load(test_data.id)
