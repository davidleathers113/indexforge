"""Schema management foundation for IndexForge.

This module provides the core abstractions and protocols for schema management,
including schema validation, versioning, and inheritance support.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Set, TypeVar

from pydantic import BaseModel, Field


class SchemaType(str, Enum):
    """Enumeration of supported schema types."""

    DOCUMENT = "document"
    CHUNK = "chunk"
    REFERENCE = "reference"
    METADATA = "metadata"


class ValidationError(Exception):
    """Raised when schema validation fails."""

    def __init__(
        self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        self.field = field
        self.details = details or {}
        super().__init__(message)


class SchemaVersion(BaseModel):
    """Represents a schema version with metadata."""

    major: int = Field(ge=0, description="Major version number")
    minor: int = Field(ge=0, description="Minor version number")
    patch: int = Field(ge=0, description="Patch version number")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    description: str = Field(default="", description="Version change description")

    def __lt__(self, other: "SchemaVersion") -> bool:
        """Compare versions for ordering."""
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    @property
    def is_breaking_change(self) -> bool:
        """Check if this version represents a breaking change."""
        return self.major > 0


class SchemaValidator(Protocol):
    """Protocol defining schema validation interface."""

    def validate(self, data: Dict[str, Any]) -> List[ValidationError]:
        """Validate data against schema.

        Args:
            data: The data to validate against the schema.

        Returns:
            List of validation errors, empty if validation succeeds.
        """
        ...


T = TypeVar("T", bound="BaseSchema")


class BaseSchema(ABC):
    """Base class for all schema definitions."""

    def __init__(
        self,
        name: str,
        version: SchemaVersion,
        schema_type: SchemaType,
        fields: Dict[str, Any],
        required_fields: Optional[Set[str]] = None,
        validators: Optional[List[SchemaValidator]] = None,
        description: str = "",
    ):
        """Initialize schema.

        Args:
            name: Unique name identifying the schema
            version: Schema version information
            schema_type: Type of schema (document, chunk, etc.)
            fields: Dictionary of field definitions
            required_fields: Set of required field names
            validators: List of custom validators
            description: Schema description
        """
        self.name = name
        self.version = version
        self.schema_type = schema_type
        self.fields = fields
        self.required_fields = required_fields or set()
        self.validators = validators or []
        self.description = description

    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> List[ValidationError]:
        """Validate data against this schema.

        Args:
            data: The data to validate

        Returns:
            List of validation errors, empty if validation succeeds
        """
        ...

    @abstractmethod
    def is_compatible(self, other: T) -> bool:
        """Check if this schema is compatible with another schema.

        Args:
            other: Another schema to check compatibility with

        Returns:
            True if schemas are compatible, False otherwise
        """
        ...

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary representation.

        Returns:
            Dictionary representation of the schema
        """
        ...

    @classmethod
    @abstractmethod
    def from_dict(cls: type[T], data: Dict[str, Any]) -> T:
        """Create schema instance from dictionary representation.

        Args:
            data: Dictionary representation of schema

        Returns:
            New schema instance
        """
        ...
