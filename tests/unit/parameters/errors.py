"""Mock error classes for parameter tests."""


class ValidationError(Exception):
    """Mock of ValidationError for testing."""

    def __init__(self, message: str, parameter_name: str | None = None):
        self.parameter_name = parameter_name
        super().__init__(message)
