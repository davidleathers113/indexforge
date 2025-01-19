"""Base model definitions for text processing."""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass
class ProcessingMetadata:
    """Metadata for processing operations.

    This class stores metadata about processing operations,
    including timing, resource usage, and custom attributes.

    Attributes:
        operation_id: Unique identifier for the processing operation
        start_time: Operation start timestamp
        end_time: Operation end timestamp
        resource_usage: Resource consumption metrics
        custom_attributes: Additional metadata key-value pairs
    """

    operation_id: UUID = field(default_factory=uuid4)
    start_time: float | None = None
    end_time: float | None = None
    resource_usage: dict[str, float] = field(default_factory=dict)
    custom_attributes: dict[str, Any] = field(default_factory=dict)

    def add_attribute(self, key: str, value: Any) -> None:
        """Add a custom attribute.

        Args:
            key: Attribute key
            value: Attribute value

        Raises:
            ValueError: If key is invalid
        """
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")
        self.custom_attributes[key] = value

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get a custom attribute value.

        Args:
            key: Attribute key
            default: Default value if key not found

        Returns:
            Attribute value or default
        """
        return self.custom_attributes.get(key, default)


@dataclass
class ProcessingContext:
    """Context for processing operations.

    This class provides context for processing operations,
    including configuration, state, and metadata.

    Attributes:
        metadata: Processing metadata
        config: Processing configuration
        state: Current processing state
    """

    metadata: ProcessingMetadata = field(default_factory=ProcessingMetadata)
    config: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)

    def update_config(self, updates: dict[str, Any]) -> None:
        """Update configuration values.

        Args:
            updates: Dictionary of configuration updates
        """
        self.config.update(updates)

    def set_state(self, key: str, value: Any) -> None:
        """Set a state value.

        Args:
            key: State key
            value: State value

        Raises:
            ValueError: If key is invalid
        """
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")
        self.state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state value.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value or default
        """
        return self.state.get(key, default)
