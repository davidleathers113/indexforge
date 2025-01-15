"""Parameter factory implementation."""

from typing import Any, Dict, Optional, Union

from src.pipeline.parameters.types.cache import CacheConfig, CacheParameter
from src.pipeline.parameters.types.numeric import NumericParameter
from src.pipeline.parameters.types.string import StringParameter
from src.pipeline.parameters.types.url import URLParameter


class ParameterFactory:
    """Factory for creating parameter instances."""

    @staticmethod
    def create_string_parameter(
        name: str,
        value: Union[str, bytes],
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        required: bool = True,
        allow_none: bool = False,
        description: Optional[str] = None,
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
        value: Union[int, float, str],
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        required: bool = True,
        allow_none: bool = False,
        description: Optional[str] = None,
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
        allowed_schemes: Optional[list[str]] = None,
        required: bool = True,
        allow_none: bool = False,
        description: Optional[str] = None,
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
        value: Optional[Union[CacheConfig, Dict[str, Any]]] = None,
        required: bool = False,
        description: Optional[str] = None,
    ) -> CacheParameter:
        """Create a cache parameter."""
        return CacheParameter(
            name=name,
            value=value,
            required=required,
            description=description,
        )
