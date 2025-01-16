"""Common test mock utility functions."""

from typing import Any


__all__ = [
    "MockResponse",
    "create_mock_response",
]


class MockResponse:
    """Mock HTTP response."""

    def __init__(
        self,
        status_code: int = 200,
        json_data: dict[str, Any] | None = None,
        text: str | None = None,
    ) -> None:
        """Initialize the mock response."""
        self.status_code = status_code
        self._json_data = json_data
        self._text = text

    @property
    def text(self) -> str:
        """Get response text."""
        if self._text is not None:
            return self._text
        if self._json_data is not None:
            import json

            return json.dumps(self._json_data)
        return ""

    def json(self) -> dict[str, Any]:
        """Get response JSON."""
        if self._json_data is not None:
            return self._json_data
        import json

        return json.loads(self._text) if self._text else {}


def create_mock_response(
    status_code: int = 200,
    json_data: dict[str, Any] | None = None,
    text: str | None = None,
) -> MockResponse:
    """Create a mock HTTP response."""
    return MockResponse(status_code=status_code, json_data=json_data, text=text)
