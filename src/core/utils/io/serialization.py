"""Serialization utilities.

This module provides utilities for JSON serialization and deserialization with support
for custom types and error handling.
"""

import json
from datetime import datetime
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T")


class SerializationError(Exception):
    """Base class for serialization errors."""

    pass


class JsonLoadError(SerializationError):
    """Error loading JSON data."""

    pass


class JsonSaveError(SerializationError):
    """Error saving JSON data."""

    pass


class DateParseError(SerializationError):
    """Error parsing date string."""

    pass


class JsonHandler:
    """Utility class for JSON serialization with custom type support."""

    DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

    @classmethod
    def serialize(cls, obj: Any) -> Dict[str, Any]:
        """Serialize an object to a JSON-compatible dictionary.

        Args:
            obj: Object to serialize

        Returns:
            JSON-compatible dictionary

        Raises:
            JsonSaveError: If serialization fails
        """
        try:
            if isinstance(obj, datetime):
                return {"__type__": "datetime", "value": obj.strftime(cls.DATE_FORMAT)}
            if hasattr(obj, "__dict__"):
                return {
                    "__type__": obj.__class__.__name__,
                    "value": {k: cls.serialize(v) for k, v in obj.__dict__.items()},
                }
            if isinstance(obj, (list, tuple)):
                return [cls.serialize(item) for item in obj]
            if isinstance(obj, dict):
                return {k: cls.serialize(v) for k, v in obj.items()}
            return obj
        except Exception as e:
            raise JsonSaveError(f"Failed to serialize object: {str(e)}") from e

    @classmethod
    def deserialize(
        cls, data: Dict[str, Any], type_registry: Dict[str, Type[T]] | None = None
    ) -> Any:
        """Deserialize a dictionary to an object.

        Args:
            data: Dictionary to deserialize
            type_registry: Optional mapping of type names to classes

        Returns:
            Deserialized object

        Raises:
            JsonLoadError: If deserialization fails
            DateParseError: If date parsing fails
        """
        if not isinstance(data, dict):
            return data

        try:
            if "__type__" in data:
                type_name = data["__type__"]
                if type_name == "datetime":
                    try:
                        return datetime.strptime(data["value"], cls.DATE_FORMAT)
                    except ValueError as e:
                        raise DateParseError(f"Failed to parse date: {str(e)}") from e

                if type_registry and type_name in type_registry:
                    cls_type = type_registry[type_name]
                    if hasattr(cls_type, "from_dict"):
                        return cls_type.from_dict(cls.deserialize(data["value"], type_registry))
                    obj = cls_type()
                    for k, v in data["value"].items():
                        setattr(obj, k, cls.deserialize(v, type_registry))
                    return obj

            return {k: cls.deserialize(v, type_registry) for k, v in data.items()}
        except (KeyError, AttributeError, TypeError) as e:
            raise JsonLoadError(f"Failed to deserialize object: {str(e)}") from e

    @classmethod
    def to_json(cls, obj: Any, indent: int | None = None) -> str:
        """Convert an object to a JSON string.

        Args:
            obj: Object to convert
            indent: Optional indentation level

        Returns:
            JSON string

        Raises:
            JsonSaveError: If conversion fails
        """
        try:
            return json.dumps(cls.serialize(obj), indent=indent)
        except Exception as e:
            raise JsonSaveError(f"Failed to convert to JSON: {str(e)}") from e

    @classmethod
    def from_json(cls, json_str: str, type_registry: Dict[str, Type[T]] | None = None) -> Any:
        """Convert a JSON string to an object.

        Args:
            json_str: JSON string to convert
            type_registry: Optional mapping of type names to classes

        Returns:
            Deserialized object

        Raises:
            JsonLoadError: If conversion fails
        """
        try:
            data = json.loads(json_str)
            return cls.deserialize(data, type_registry)
        except json.JSONDecodeError as e:
            raise JsonLoadError(f"Failed to parse JSON: {str(e)}") from e
