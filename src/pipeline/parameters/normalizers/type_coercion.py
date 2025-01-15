"""Type coercion normalizer implementation."""

import logging
from typing import Any, Generic, Optional, Type, TypeVar

from src.pipeline.errors import ValidationError
from src.pipeline.parameters.normalizers.base import Normalizer

T = TypeVar("T")


class TypeCoercionNormalizer(Normalizer[Any, Optional[T]], Generic[T]):
    """Normalizer for type coercion."""

    def __init__(self, target_type: Type[T], allow_none: bool = False):
        self.target_type = target_type
        self.allow_none = allow_none
        self.logger = logging.getLogger(__name__)

    def normalize(self, value: Any) -> Optional[T]:
        """Normalize a value by coercing it to the target type.

        Args:
            value: Value to normalize

        Returns:
            Normalized value

        Raises:
            ValidationError: If value cannot be coerced to target type
        """
        try:
            if value is None and self.allow_none:
                self.logger.debug("None value allowed")
                return value

            if isinstance(value, self.target_type):
                return value

            if issubclass(self.target_type, str):
                result = str(value)
                self.logger.debug(f"Coerced to string: {result}")
                return result

            if issubclass(self.target_type, int):
                if isinstance(value, str):
                    value = value.strip()
                result = int(float(value))
                self.logger.debug(f"Coerced to int: {result}")
                return result

            if issubclass(self.target_type, float):
                if isinstance(value, str):
                    value = value.strip()
                result = float(value)
                self.logger.debug(f"Coerced to float: {result}")
                return result

            return value

        except (ValueError, TypeError) as e:
            self.logger.error(f"Failed to coerce to {self.target_type.__name__}: {str(e)}")
            raise ValidationError(
                f"Value must be {self.target_type.__name__}, got {type(value).__name__}"
            )
