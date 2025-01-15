"""Base classes for parameter management."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar

from src.pipeline.errors import ValidationError

T = TypeVar("T")


class Parameter(ABC):
    """Base class for all parameter types."""

    def __init__(
        self,
        name: str,
        value: Any,
        required: bool = True,
        allow_none: bool = False,
        description: Optional[str] = None,
    ):
        self.name = name
        self._value = value
        self.required = required
        self.allow_none = allow_none
        self.description = description or f"Parameter {name}"

    @property
    def value(self) -> Any:
        """Get the parameter value."""
        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        """Set the parameter value."""
        self._value = new_value

    @abstractmethod
    def validate(self) -> None:
        """Validate the parameter value.

        Raises:
            ValidationError: If validation fails
        """
        if self.required and self._value is None:
            raise ValidationError(f"Parameter {self.name} is required")
        if self._value is None and not self.allow_none:
            raise ValidationError(f"Parameter {self.name} cannot be None")

    @abstractmethod
    def normalize(self) -> Any:
        """Normalize the parameter value.

        Returns:
            Normalized value
        """
        return self._value


class ParameterSet:
    """Container for a set of parameters."""

    def __init__(self):
        self._parameters: Dict[str, Parameter] = {}

    def add_parameter(self, parameter: Parameter) -> None:
        """Add a parameter to the set."""
        self._parameters[parameter.name] = parameter

    def get_parameter(self, name: str) -> Optional[Parameter]:
        """Get a parameter by name."""
        return self._parameters.get(name)

    def validate_all(self) -> None:
        """Validate all parameters."""
        errors: List[str] = []
        for param in self._parameters.values():
            try:
                param.validate()
            except ValidationError as e:
                errors.append(str(e))
        if errors:
            raise ValidationError("\n".join(errors))

    def normalize_all(self) -> Dict[str, Any]:
        """Normalize all parameters."""
        return {name: param.normalize() for name, param in self._parameters.items()}
