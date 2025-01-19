"""String parameter type implementation."""


from src.pipeline.parameters.base import Parameter
from src.pipeline.parameters.normalizers.type_coercion import TypeCoercionNormalizer
from src.pipeline.parameters.validators.string import StringValidator


class StringParameter(Parameter):
    """Parameter type for string values."""

    def __init__(
        self,
        name: str,
        value: str | bytes,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        required: bool = True,
        allow_none: bool = False,
        description: str | None = None,
    ):
        super().__init__(name, value, required, allow_none, description)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.validator = StringValidator(min_length, max_length, pattern)
        self.normalizer = TypeCoercionNormalizer(str, allow_none=allow_none)

    def validate(self) -> None:
        """Validate the string parameter."""
        super().validate()
        if self._value is not None:
            self.validator.validate(self._value, self.name)

    def normalize(self) -> str | None:
        """Normalize the string value."""
        if self._value is None:
            return None
        if isinstance(self._value, bytes):
            return self._value.decode("utf-8").strip()
        return self.normalizer.normalize(self._value)
