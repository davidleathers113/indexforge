"""JSON-based storage implementation.

This module provides a JSON-based implementation of the storage strategy,
handling serialization and storage of data in JSON format. It includes
support for custom type serialization and atomic file operations.

Key Features:
    - JSON serialization
    - Custom type handling
    - UTC datetime support
    - Atomic file operations
    - Path normalization
"""

from __future__ import annotations

from datetime import datetime
import json
import logging
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID


if TYPE_CHECKING:
    from pathlib import Path

from src.core.storage.strategies.base import (
    BaseStorage,
    DataCorruptionError,
    SerializationStrategy,
    StorageError,
)


logger = logging.getLogger(__name__)

T = TypeVar("T")


class JsonSerializationError(StorageError):
    """Raised when JSON serialization/deserialization fails."""


class JsonDeserializationError(JsonSerializationError):
    """Raised when JSON deserialization fails for a specific field."""

    def __init__(self, field: str, value: Any, reason: str) -> None:
        """Initialize error.

        Args:
            field: Name of field that failed to deserialize
            value: Value that could not be deserialized
            reason: Reason for failure
        """
        super().__init__(f"Failed to deserialize field '{field}' with value '{value}': {reason}")
        self.field = field
        self.value = value
        self.reason = reason


class JsonSerializer(SerializationStrategy[T]):
    """JSON serialization implementation."""

    def __init__(self, model_type: type[T]) -> None:
        """Initialize serializer.

        Args:
            model_type: Type of model to serialize
        """
        self.model_type = model_type

    def _serialize_value(self, obj: Any) -> Any:
        """Serialize a single value.

        Args:
            obj: Value to serialize

        Returns:
            JSON-serializable value

        Raises:
            JsonSerializationError: If value cannot be serialized
        """
        try:
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, UUID):
                return str(obj)
            if hasattr(obj, "to_dict"):
                return obj.to_dict()
            return obj
        except Exception as e:
            raise JsonSerializationError(f"Failed to serialize value '{obj}': {e}") from e

    def _deserialize_value(self, value: Any, key: str) -> Any:
        """Deserialize a single value.

        Args:
            value: Value to deserialize
            key: Field name for context in error messages

        Returns:
            Deserialized value

        Raises:
            JsonDeserializationError: If value cannot be deserialized
        """
        if isinstance(value, str):
            # Try parsing as datetime
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                # Try parsing as UUID
                try:
                    return UUID(value)
                except (ValueError, AttributeError):
                    # Not a datetime or UUID, return as string
                    return value
        elif isinstance(value, dict) and hasattr(self.model_type, "from_dict"):
            # Handle nested objects
            try:
                return self.model_type.from_dict(value)
            except Exception as e:
                raise JsonDeserializationError(key, value, f"Invalid nested object: {e}")
        return value

    def serialize(self, data: T) -> bytes:
        """Serialize data to JSON bytes.

        Args:
            data: Data to serialize

        Returns:
            JSON bytes

        Raises:
            JsonSerializationError: If serialization fails
        """
        try:
            if hasattr(data, "to_dict"):
                serialized = data.to_dict()
            elif isinstance(data, dict):
                serialized = {k: self._serialize_value(v) for k, v in data.items()}
            else:
                raise JsonSerializationError(f"Cannot serialize type: {type(data)}")

            return json.dumps(serialized, indent=2).encode()

        except Exception as e:
            logger.exception("JSON serialization failed")
            raise JsonSerializationError(f"Failed to serialize data: {e}") from e

    def deserialize(self, data: bytes) -> T:
        """Deserialize JSON bytes to data.

        Args:
            data: JSON bytes to deserialize

        Returns:
            Deserialized data

        Raises:
            DataCorruptionError: If data is corrupted
            JsonSerializationError: If deserialization fails
        """
        try:
            raw_data = json.loads(data.decode())

            if not isinstance(raw_data, dict):
                raise DataCorruptionError("JSON data must be an object")

            # Convert values with detailed error handling
            processed_data = {}
            for key, value in raw_data.items():
                try:
                    processed_data[key] = self._deserialize_value(value, key)
                except JsonDeserializationError:
                    raise
                except Exception as e:
                    raise JsonDeserializationError(key, value, str(e))

            # Create instance with validation
            try:
                if hasattr(self.model_type, "from_dict"):
                    return self.model_type.from_dict(processed_data)
                return self.model_type(**processed_data)
            except Exception as e:
                raise DataCorruptionError(
                    f"Failed to create {self.model_type.__name__}: {e}"
                ) from e

        except json.JSONDecodeError as e:
            raise DataCorruptionError(f"Invalid JSON data: {e}") from e
        except (DataCorruptionError, JsonDeserializationError):
            raise
        except Exception as e:
            logger.exception("JSON deserialization failed")
            raise JsonSerializationError(f"Failed to deserialize data: {e}") from e


class JsonStorage(BaseStorage[T]):
    """JSON file storage implementation."""

    def __init__(
        self, storage_path: Path, model_type: type[T], *, extension: str = ".json"
    ) -> None:
        """Initialize JSON storage.

        Args:
            storage_path: Path to storage directory
            model_type: Type of model to store
            extension: File extension for stored files
        """
        super().__init__(storage_path, JsonSerializer(model_type))
        self.extension = extension

    def _get_path(self, key: str) -> Path:
        """Get path for a specific key.

        Args:
            key: Data identifier

        Returns:
            Path to the JSON file
        """
        # Normalize key to valid filename
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return self.storage_path / f"{safe_key}{self.extension}"
