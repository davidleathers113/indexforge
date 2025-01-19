"""URL value validator implementation."""

import logging
from urllib.parse import urlparse, urlunparse

from src.pipeline.errors import ValidationError
from src.pipeline.parameters.validators.base import Validator


class URLValidator(Validator):
    """Validator for URL values."""

    def __init__(
        self,
        allowed_schemes: list[str] | None = None,
        require_path: bool = False,
        allow_query: bool = True,
        allow_fragment: bool = True,
    ):
        self.allowed_schemes = allowed_schemes or ["http", "https"]
        self.require_path = require_path
        self.allow_query = allow_query
        self.allow_fragment = allow_fragment
        self.logger = logging.getLogger(__name__)

    def validate(self, value: str, param_name: str) -> None:
        """Validate a URL value.

        Args:
            value: Value to validate
            param_name: Name of the parameter being validated

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError(f"{param_name} must be a string URL, got {type(value).__name__}")

        try:
            parsed = urlparse(value.strip())

            if not parsed.scheme:
                raise ValidationError(f"{param_name} must include a scheme (e.g., http://)")

            if parsed.scheme not in self.allowed_schemes:
                raise ValidationError(
                    f"{param_name} scheme must be one of: {', '.join(self.allowed_schemes)}"
                )

            if not parsed.netloc:
                raise ValidationError(f"{param_name} must include a host")

            if " " in parsed.netloc:
                raise ValidationError(f"{param_name} host cannot contain spaces")

            if "//" in parsed.path:
                raise ValidationError(f"{param_name} path cannot contain double slashes")

            if self.require_path and not parsed.path:
                raise ValidationError(f"{param_name} must include a path")

            if not self.allow_query and parsed.query:
                raise ValidationError(f"{param_name} cannot include query parameters")

            if not self.allow_fragment and parsed.fragment:
                raise ValidationError(f"{param_name} cannot include fragments")

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Invalid URL format for {param_name}: {e!s}")

    def normalize(self, value: str) -> str:
        """Normalize a URL value.

        Args:
            value: URL to normalize

        Returns:
            Normalized URL string
        """
        try:
            parsed = urlparse(value)
            scheme = parsed.scheme.lower()
            path = parsed.path.rstrip("/")  # Remove trailing slash without adding /
            normalized = urlunparse((scheme, parsed.netloc, path, "", "", ""))
            self.logger.debug(f"Normalized URL {value} to {normalized}")
            return normalized
        except Exception as e:
            self.logger.warning(f"Failed to normalize URL {value}: {e!s}")
            return value
