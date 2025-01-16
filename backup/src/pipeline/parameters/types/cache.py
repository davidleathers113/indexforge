"""Cache parameter type implementation."""

from dataclasses import dataclass

from src.pipeline.parameters.base import Parameter
from src.pipeline.parameters.validators.numeric import NumericValidator
from src.pipeline.parameters.validators.string import StringValidator


@dataclass
class CacheConfig:
    """Cache configuration container."""

    host: str | None = None
    port: int | None = None
    ttl: int | None = None


class CacheParameter(Parameter):
    """Parameter type for cache configuration."""

    def __init__(
        self,
        name: str,
        value: CacheConfig | None = None,
        required: bool = False,
        description: str | None = None,
    ):
        super().__init__(name, value, required, True, description)
        self.host_validator = StringValidator()
        self.port_validator = NumericValidator(min_value=0, max_value=65535)
        self.ttl_validator = NumericValidator(min_value=0)

    def validate(self) -> None:
        """Validate the cache parameter."""
        super().validate()
        if self._value is not None:
            if not isinstance(self._value, CacheConfig):
                self._value = self._to_config(self._value)

            if self._value.host is not None:
                self.host_validator.validate(self._value.host, f"{self.name}_host")

            if self._value.port is not None:
                self.port_validator.validate(self._value.port, f"{self.name}_port")

            if self._value.ttl is not None:
                self.ttl_validator.validate(self._value.ttl, f"{self.name}_ttl")

    def normalize(self) -> CacheConfig | None:
        """Normalize the cache configuration."""
        if self._value is None:
            return None

        if not isinstance(self._value, CacheConfig):
            self._value = self._to_config(self._value)

        return CacheConfig(
            host=str(self._value.host).strip() if self._value.host is not None else None,
            port=int(self._value.port) if self._value.port is not None else None,
            ttl=int(self._value.ttl) if self._value.ttl is not None else None,
        )

    def _to_config(self, value: any) -> CacheConfig:
        """Convert a value to CacheConfig."""
        if isinstance(value, dict):
            return CacheConfig(
                host=value.get("host"),
                port=value.get("port"),
                ttl=value.get("ttl"),
            )
        return CacheConfig()
