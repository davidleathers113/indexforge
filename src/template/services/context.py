"""Template context service.

This module is responsible for:
1. Providing template context generation
2. Managing setup and verification helpers
3. Supporting test code generation
"""

import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """Supported template types."""

    CACHE = auto()
    RETRY = auto()
    LOG = auto()
    MOCK = auto()


@dataclass
class CacheConfig:
    """Configuration for cache mock setup and verification."""

    method: str = "get"  # get or set
    key: str = "test_key"
    value: Any = None
    return_value: Any = None


@dataclass
class RetryConfig:
    """Configuration for retry mock setup and verification."""

    max_retries: int = 3
    success_on: int = 2
    error_type: str = "ValueError"
    error_message: str = "Retry failed"


@dataclass
class SerializationConfig:
    """Configuration for serialization mock setup."""

    dumps_return: bytes = b"serialized"
    loads_return: Any = "deserialized"


class SetupHelpers:
    """Helpers for generating test setup code."""

    def setup_cache_mock(self, config: Optional[CacheConfig] = None) -> str:
        """Generates code for creating a cache mock.

        Args:
            config: Optional cache configuration

        Returns:
            Python code string for creating the mock
        """
        if not config:
            config = CacheConfig()

        return f"""
# Create cache mock
mock_cache = Mock()
mock_cache.{config.method}.return_value = {config.return_value!r}
""".strip()

    def setup_serialization(self, config: Optional[SerializationConfig] = None) -> str:
        """Generates code for creating a serialization mock.

        Args:
            config: Optional serialization configuration

        Returns:
            Python code string for creating the mock
        """
        if not config:
            config = SerializationConfig()

        return f"""
# Create serializer mock
mock_serializer = Mock()
mock_serializer.dumps.return_value = {config.dumps_return!r}
mock_serializer.loads.return_value = {config.loads_return!r}
""".strip()

    def setup_retry_mocks(self, config: Optional[RetryConfig] = None) -> str:
        """Generates code for creating retry mocks.

        Args:
            config: Optional retry configuration

        Returns:
            Python code string for creating the mock
        """
        if not config:
            config = RetryConfig()

        return f"""
# Create retry mock with configurable behavior
mock_retry = Mock()
attempts = [0]  # Mutable counter

def retry_side_effect(*args, **kwargs):
    attempts[0] += 1
    if attempts[0] >= {config.success_on}:
        return True
    raise {config.error_type}({config.error_message!r})

mock_retry.side_effect = retry_side_effect
""".strip()


class VerificationHelpers:
    """Helpers for generating test verification code."""

    def verify_result(self, actual: str, expected: Any, message: Optional[str] = None) -> str:
        """Generates code to verify a result.

        Args:
            actual: Variable name containing actual result
            expected: Expected value
            message: Optional assertion message

        Returns:
            Python code string for verification
        """
        msg = f", {message!r}" if message else ""
        return f"assert {actual} == {expected!r}{msg}"

    def verify_retry_behavior(self, mock_name: str, config: RetryConfig) -> str:
        """Generates code to verify retry behavior.

        Args:
            mock_name: Name of the retry mock variable
            config: Retry configuration

        Returns:
            Python code string for verification
        """
        return f"""
# Verify retry attempts
assert {mock_name}.call_count == {config.success_on}, (
    f"Expected {config.success_on} retry attempts, "
    f"got {{{mock_name}.call_count}}"
)
""".strip()

    def verify_cache_call(self, mock_name: str, config: CacheConfig) -> str:
        """Generates code to verify cache method calls.

        Args:
            mock_name: Name of the cache mock variable
            config: Cache configuration

        Returns:
            Python code string for verification
        """
        if config.method == "set":
            args = f"({config.key!r}, {config.value!r})"
        else:
            args = f"({config.key!r},)"

        return f"""
# Verify cache {config.method} call
method_mock = {mock_name}.{config.method}
assert method_mock.call_args == ({args}, {{}})
""".strip()

    def verify_serialization_calls(self, mock_name: str, calls: List[Dict[str, Any]]) -> str:
        """Generates code to verify serialization calls.

        Args:
            mock_name: Name of the serializer mock variable
            calls: List of expected calls with method and args

        Returns:
            Python code string for verification
        """
        verifications = []
        for i, call in enumerate(calls):
            method = call["method"]
            args = call.get("args", [])
            kwargs = call.get("kwargs", {})
            verifications.append(
                f"assert {mock_name}.{method}.call_args_list[{i}] == "
                f"(({', '.join(map(repr, args))},), {kwargs!r})"
            )

        return "\n".join(verifications)

    def verify_single_log(
        self, mock_name: str, level: str, message: str, call_number: int = -1
    ) -> str:
        """Generates code to verify a log message.

        Args:
            mock_name: Name of the logger mock variable
            level: Log level (info, error, etc.)
            message: Expected message content
            call_number: Which call to verify (-1 for latest)

        Returns:
            Python code string for verification
        """
        return f"""
# Verify log message
log_method = {mock_name}.{level.lower()}
assert {message!r} in log_method.call_args_list[{call_number}][0][0]
""".strip()


class ContextService:
    """Service for managing template contexts.

    This class is responsible for:
    1. Providing template context generation
    2. Managing setup and verification helpers
    3. Supporting test code generation
    """

    def __init__(self):
        """Initialize the context service."""
        self._setup = SetupHelpers()
        self._verify = VerificationHelpers()

    def get_context(self, template_type: str, **kwargs) -> Dict[str, Any]:
        """Gets context for template rendering.

        Args:
            template_type: Type of template being rendered
            **kwargs: Additional context variables

        Returns:
            Template context dictionary

        Raises:
            ValueError: If template_type is not valid
        """
        logger.debug(f"Generating context for template type: {template_type}")

        try:
            template_enum = TemplateType[template_type.upper()]
        except KeyError:
            valid_types = ", ".join(t.name for t in TemplateType)
            error_msg = f"Invalid template type: {template_type}. Must be one of: {valid_types}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Create base context with helpers
        context = self._create_base_context()

        # Add template-specific context
        if template_enum == TemplateType.CACHE:
            context.update(self._get_cache_context())
        elif template_enum == TemplateType.RETRY:
            context.update(self._get_retry_context())
        elif template_enum == TemplateType.LOG:
            context.update(self._get_log_context())
        elif template_enum == TemplateType.MOCK:
            context.update(self._get_mock_context())

        # Update with user-provided context
        context.update(kwargs)
        logger.debug(f"Generated context with keys: {list(context.keys())}")
        return context

    def _create_base_context(self) -> Dict[str, Any]:
        """Creates base context with all helpers.

        Returns:
            Dictionary containing helper methods
        """
        return {
            # Setup helpers
            "setup_cache": self._setup.setup_cache_mock,
            "setup_serialization": self._setup.setup_serialization,
            "setup_retry": self._setup.setup_retry_mocks,
            # Verification helpers
            "verify_result": self._verify.verify_result,
            "verify_retry": self._verify.verify_retry_behavior,
            "verify_cache": self._verify.verify_cache_call,
            "verify_serialization": self._verify.verify_serialization_calls,
            "verify_log": self._verify.verify_single_log,
        }

    def _get_cache_context(self) -> Dict[str, Any]:
        """Gets context for cache templates.

        Returns:
            Cache-specific context dictionary
        """
        return {
            "CacheConfig": CacheConfig,
            "default_key": "cache_key",
            "default_value": "cached_value",
        }

    def _get_retry_context(self) -> Dict[str, Any]:
        """Gets context for retry templates.

        Returns:
            Retry-specific context dictionary
        """
        return {
            "RetryConfig": RetryConfig,
            "default_max_retries": 3,
            "default_error": ValueError("Retry failed"),
        }

    def _get_log_context(self) -> Dict[str, Any]:
        """Gets context for log templates.

        Returns:
            Log-specific context dictionary
        """
        return {
            "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "default_level": "INFO",
            "default_format": "%(levelname)s: %(message)s",
        }

    def _get_mock_context(self) -> Dict[str, Any]:
        """Gets context for mock templates.

        Returns:
            Mock-specific context dictionary
        """
        return {
            "SerializationConfig": SerializationConfig,
            "default_return_value": None,
            "default_side_effect": None,
        }
