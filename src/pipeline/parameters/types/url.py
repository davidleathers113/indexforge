"""URL parameter type implementation."""

from typing import Optional

from src.pipeline.parameters.base import Parameter
from src.pipeline.parameters.normalizers.url import URLNormalizer
from src.pipeline.parameters.validators.url import URLValidator


class URLParameter(Parameter):
    """Parameter type for URL values."""

    def __init__(
        self,
        name: str,
        value: str,
        required: bool = True,
        allow_none: bool = False,
        description: Optional[str] = None,
        allowed_schemes: Optional[list[str]] = None,
    ):
        super().__init__(name, value, required, allow_none, description)
        self.allowed_schemes = allowed_schemes or ["http", "https"]
        self.validator = URLValidator(allowed_schemes=self.allowed_schemes)
        self.normalizer = URLNormalizer()

    def validate(self) -> None:
        """Validate the URL parameter."""
        super().validate()
        if self._value is not None:
            self.validator.validate(self._value, self.name)

    def normalize(self) -> Optional[str]:
        """Normalize the URL value."""
        if self._value is None:
            return None
        return self.normalizer.normalize(str(self._value))
