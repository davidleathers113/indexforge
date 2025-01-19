"""Numeric parameter type implementation."""


from src.pipeline.parameters.base import Parameter
from src.pipeline.parameters.normalizers.type_coercion import TypeCoercionNormalizer
from src.pipeline.parameters.validators.numeric import NumericValidator


class NumericParameter(Parameter):
    """Parameter type for numeric values."""

    def __init__(
        self,
        name: str,
        value: int | float | str,
        min_value: int | float | None = None,
        max_value: int | float | None = None,
        required: bool = True,
        allow_none: bool = False,
        description: str | None = None,
    ):
        super().__init__(name, value, required, allow_none, description)
        self.min_value = min_value
        self.max_value = max_value
        self.validator = NumericValidator(min_value, max_value)
        self.normalizer = TypeCoercionNormalizer(int, allow_none=allow_none)

    def validate(self) -> None:
        """Validate the numeric parameter."""
        super().validate()
        if self._value is not None:
            self.validator.validate(self._value, self.name)

    def normalize(self) -> int | float | None:
        """Normalize the numeric value."""
        if self._value is None:
            return None
        return self.normalizer.normalize(self._value)
