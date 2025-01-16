"""Parameter builder implementation."""

from typing import Any

from src.pipeline.parameters.base import ParameterSet
from src.pipeline.parameters.factory import ParameterFactory
from src.pipeline.parameters.types.cache import CacheConfig


class ParameterBuilder:
    """Builder for creating parameter sets."""

    def __init__(self):
        self.parameter_set = ParameterSet()
        self.factory = ParameterFactory()

    def add_string_parameter(
        self,
        name: str,
        value: str | bytes,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        required: bool = True,
        allow_none: bool = False,
        description: str | None = None,
    ) -> "ParameterBuilder":
        """Add a string parameter."""
        param = self.factory.create_string_parameter(
            name=name,
            value=value,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            required=required,
            allow_none=allow_none,
            description=description,
        )
        self.parameter_set.add_parameter(param)
        return self

    def add_numeric_parameter(
        self,
        name: str,
        value: int | float | str,
        min_value: int | float | None = None,
        max_value: int | float | None = None,
        required: bool = True,
        allow_none: bool = False,
        description: str | None = None,
    ) -> "ParameterBuilder":
        """Add a numeric parameter."""
        param = self.factory.create_numeric_parameter(
            name=name,
            value=value,
            min_value=min_value,
            max_value=max_value,
            required=required,
            allow_none=allow_none,
            description=description,
        )
        self.parameter_set.add_parameter(param)
        return self

    def add_url_parameter(
        self,
        name: str,
        value: str,
        allowed_schemes: list[str] | None = None,
        required: bool = True,
        allow_none: bool = False,
        description: str | None = None,
    ) -> "ParameterBuilder":
        """Add a URL parameter."""
        param = self.factory.create_url_parameter(
            name=name,
            value=value,
            allowed_schemes=allowed_schemes,
            required=required,
            allow_none=allow_none,
            description=description,
        )
        self.parameter_set.add_parameter(param)
        return self

    def add_cache_parameter(
        self,
        name: str = "cache",
        value: CacheConfig | dict[str, Any] | None = None,
        required: bool = False,
        description: str | None = None,
    ) -> "ParameterBuilder":
        """Add a cache parameter."""
        param = self.factory.create_cache_parameter(
            name=name,
            value=value,
            required=required,
            description=description,
        )
        self.parameter_set.add_parameter(param)
        return self

    def build(self) -> ParameterSet:
        """Build and return the parameter set."""
        return self.parameter_set
