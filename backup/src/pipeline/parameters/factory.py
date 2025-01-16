"""Parameter factory implementation."""

from typing import Any

from src.pipeline.parameters.types.cache import CacheConfig, CacheParameter
from src.pipeline.parameters.types.numeric import NumericParameter
from src.pipeline.parameters.types.string import StringParameter
from src.pipeline.parameters.types.url import URLParameter


class ParameterFactory:
    """Factory for creating parameter instances."""

    @staticmethod
    def create_string_parameter(
        name: str,
        value: str | bytes,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        required: bool = True,
        allow_none: bool = False,
        description: str | None = None,
    ) -> StringParameter:
        """Create a string parameter."""
        return StringParameter(
            name=name,
            value=value,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            required=required,
            allow_none=allow_none,
            description=description,
        )

    @staticmethod
    def create_numeric_parameter(
        name: str,
        value: int | float | str,
        min_value: int | float | None = None,
        max_value: int | float | None = None,
        required: bool = True,
        allow_none: bool = False,
        description: str | None = None,
    ) -> NumericParameter:
        """Create a numeric parameter."""
        return NumericParameter(
            name=name,
            value=value,
            min_value=min_value,
            max_value=max_value,
            required=required,
            allow_none=allow_none,
            description=description,
        )

    @staticmethod
    def create_url_parameter(
        name: str,
        value: str,
        allowed_schemes: list[str] | None = None,
        required: bool = True,
        allow_none: bool = False,
        description: str | None = None,
    ) -> URLParameter:
        """Create a URL parameter."""
        return URLParameter(
            name=name,
            value=value,
            allowed_schemes=allowed_schemes,
            required=required,
            allow_none=allow_none,
            description=description,
        )

    @staticmethod
    def create_cache_parameter(
        name: str = "cache",
        value: CacheConfig | dict[str, Any] | None = None,
        required: bool = False,
        description: str | None = None,
    ) -> CacheParameter:
        """Create a cache parameter."""
        return CacheParameter(
            name=name,
            value=value,
            required=required,
            description=description,
        )
