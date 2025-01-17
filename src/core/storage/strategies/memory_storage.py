"""Memory storage strategy implementation.

This module provides an in-memory implementation of the storage strategy,
primarily intended for testing purposes. It maintains data in memory
using a dictionary and provides atomic operations through locking.

Key Features:
    - Fast in-memory storage
    - Thread-safe operations
    - Type-safe data handling
    - Simulated failures for testing
    - No persistence between runs
"""

from __future__ import annotations

import logging
import threading
from copy import deepcopy
from datetime import UTC, datetime
from typing import Dict, Generic, Type, TypeVar

from pydantic import BaseModel

from .base import DataCorruptionError, DataNotFoundError, StorageError, StorageStrategy

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class MemoryStorage(StorageStrategy[T], Generic[T]):
    """In-memory implementation of storage strategy."""

    def __init__(self, model_type: Type[T], simulate_failures: bool = False) -> None:
        """Initialize memory storage.

        Args:
            model_type: Type of model to store
            simulate_failures: Whether to simulate storage failures for testing
        """
        self._model_type = model_type
        self._simulate_failures = simulate_failures
        self._data: Dict[str, dict] = {}
        self._lock = threading.Lock()
        self._last_modified = datetime.now(UTC)
        logger.info("Initialized memory storage for %s", model_type.__name__)

    def save(self, key: str, data: T) -> None:
        """Save data to memory.

        Args:
            key: Key to store data under
            data: Data to store

        Raises:
            StorageError: If storage fails
        """
        if self._simulate_failures and key.startswith("fail"):
            raise StorageError("Simulated storage failure")

        try:
            # Validate data is of correct type
            if not isinstance(data, self._model_type):
                raise ValueError(f"Data must be instance of {self._model_type.__name__}")

            # Store copy of data dict to prevent external modification
            with self._lock:
                self._data[key] = deepcopy(data.model_dump())
                self._last_modified = datetime.now(UTC)
                logger.debug("Saved data for key: %s", key)
        except Exception as e:
            logger.error("Failed to save data for key %s: %s", key, e)
            raise StorageError(f"Failed to save data: {e}") from e

    def load(self, key: str) -> T:
        """Load data from memory.

        Args:
            key: Key to load data for

        Returns:
            Loaded data

        Raises:
            DataNotFoundError: If key not found
            DataCorruptionError: If data validation fails
            StorageError: If loading fails
        """
        if self._simulate_failures and key.startswith("fail"):
            raise StorageError("Simulated storage failure")

        try:
            with self._lock:
                data_dict = self._data.get(key)
                if data_dict is None:
                    raise DataNotFoundError(f"No data found for key: {key}")

                # Create copy of data to prevent external modification
                data_dict = deepcopy(data_dict)

            try:
                # Attempt to create model instance
                return self._model_type.model_validate(data_dict)
            except Exception as e:
                raise DataCorruptionError(f"Failed to validate data: {e}")

        except (DataNotFoundError, DataCorruptionError):
            raise
        except Exception as e:
            logger.error("Failed to load data for key %s: %s", key, e)
            raise StorageError(f"Failed to load data: {e}") from e

    def delete(self, key: str) -> None:
        """Delete data from memory.

        Args:
            key: Key to delete data for

        Raises:
            DataNotFoundError: If key not found
            StorageError: If deletion fails
        """
        if self._simulate_failures and key.startswith("fail"):
            raise StorageError("Simulated storage failure")

        try:
            with self._lock:
                if key not in self._data:
                    raise DataNotFoundError(f"No data found for key: {key}")
                del self._data[key]
                self._last_modified = datetime.now(UTC)
                logger.debug("Deleted data for key: %s", key)
        except DataNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to delete data for key %s: %s", key, e)
            raise StorageError(f"Failed to delete data: {e}") from e

    def exists(self, key: str) -> bool:
        """Check if key exists in memory.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise
        """
        with self._lock:
            return key in self._data

    def clear(self) -> None:
        """Clear all data from memory."""
        with self._lock:
            self._data.clear()
            self._last_modified = datetime.now(UTC)
            logger.debug("Cleared all data")

    def get_last_modified(self) -> datetime:
        """Get last modification time.

        Returns:
            Timestamp of last modification
        """
        with self._lock:
            return self._last_modified
