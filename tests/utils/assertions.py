"""Common test assertions."""

from typing import Any, Callable, Dict, List, Optional, Union

__all__ = [
    "assert_dict_subset",
    "assert_called_with_subset",
    "assert_logs_contain",
    "assert_redis_operations",
]


def assert_dict_subset(subset: Dict[str, Any], full_dict: Dict[str, Any]) -> None:
    """Assert that all key-value pairs in subset exist in full_dict."""
    for key, value in subset.items():
        assert key in full_dict, f"Key {key} not found in dict"
        assert full_dict[key] == value, f"Value mismatch for key {key}"


def assert_called_with_subset(mock: Any, **expected_kwargs: Any) -> None:
    """Assert that a mock was called with the expected kwargs as a subset."""
    assert mock.called, "Mock was not called"
    _, kwargs = mock.call_args
    assert_dict_subset(expected_kwargs, kwargs)


def assert_logs_contain(caplog: Any, message: str, level: Optional[str] = None) -> None:
    """Assert that logs contain a specific message at an optional level."""
    for record in caplog.records:
        if message in record.message:
            if level is None or record.levelname == level:
                return
    raise AssertionError(
        f"Log message '{message}' not found{f' at level {level}' if level else ''}"
    )


def assert_redis_operations(
    mock_redis: Any,
    expected_gets: Optional[List[str]] = None,
    expected_sets: Optional[List[tuple[str, Any, int]]] = None,
    expected_deletes: Optional[List[str]] = None,
) -> None:
    """Assert Redis operations were called with expected arguments."""
    if expected_gets:
        assert mock_redis.get.call_count == len(expected_gets)
        for key in expected_gets:
            mock_redis.get.assert_any_call(key)

    if expected_sets:
        assert mock_redis.setex.call_count == len(expected_sets)
        for key, value, ttl in expected_sets:
            mock_redis.setex.assert_any_call(key, ttl, value)

    if expected_deletes:
        assert mock_redis.delete.call_count == len(expected_deletes)
        for key in expected_deletes:
            mock_redis.delete.assert_any_call(key)


class ANY:
    """Helper class for type checking in tests."""

    def __init__(self, type_):
        self.type = type_

    def __eq__(self, other):
        return isinstance(other, self.type)

    def __repr__(self):
        return f"ANY({self.type.__name__})"
