"""Memory storage strategy implementation.

.. deprecated:: 1.0.0
    This module is deprecated and will be removed in version 2.0.0.
    Use `src.core.storage.strategies.memory_storage.storage.MemoryStorage` instead.

Migration Guide:
    1. Import the new implementation:
       ```python
       from src.core.storage.strategies.memory_storage.storage import MemoryStorage
       ```
    2. Update constructor calls to use Settings object:
       ```python
       storage = MemoryStorage(settings=settings)
       ```
    3. Replace any direct attribute access with corresponding methods

This module now re-exports the new implementation from the memory_storage package.
The original implementation has been replaced with a more comprehensive version
that provides better organization, thread safety, and memory management.
"""

from __future__ import annotations

from collections.abc import Callable
import functools
import logging
from typing import TYPE_CHECKING, Any, TypeVar, overload
import warnings

from src.core.settings import Settings
from src.core.storage.strategies.memory_storage.storage import MemoryStorage as NewMemoryStorage


if TYPE_CHECKING:
    from src.core.models.chunks import Chunk
    from src.core.models.documents import Document
    from src.core.models.references import Reference

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="Document")
C = TypeVar("C", bound="Chunk")
R = TypeVar("R", bound="Reference")


def validate_settings(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to validate settings before initialization.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function with settings validation
    """

    @functools.wraps(func)
    def wrapper(self: MemoryStorage[T, C, R], *args: Any, **kwargs: Any) -> Any:
        if "settings" in kwargs:
            settings = kwargs["settings"]
            if not isinstance(settings, Settings):
                raise TypeError("settings must be an instance of Settings")
            if not hasattr(settings, "storage"):
                raise ValueError("settings must have storage configuration")
        return func(self, *args, **kwargs)

    return wrapper


@functools.lru_cache(maxsize=128)
def create_settings_from_legacy(
    max_size_bytes: int | None = None,
    max_items: int | None = None,
) -> Settings:
    """Create settings object from legacy parameters with caching.

    Args:
        max_size_bytes: Maximum size in bytes
        max_items: Maximum number of items

    Returns:
        Settings object configured with provided parameters
    """
    return Settings(
        storage=Settings.StorageSettings(
            max_size_bytes=max_size_bytes,
            max_items=max_items,
        )
    )


class MemoryStorage(NewMemoryStorage[T, C, R]):
    """Deprecated memory storage implementation.

    This class is maintained for backward compatibility and will be removed
    in version 2.0.0. Use memory_storage.storage.MemoryStorage instead.

    Warning:
        This implementation is deprecated. While it maintains compatibility
        with existing code, new code should use the new implementation directly.

    Migration Example:
        >>> # Old usage:
        >>> storage = MemoryStorage(model_type=Document)
        >>>
        >>> # New usage:
        >>> from src.core.storage.strategies.memory_storage.storage import MemoryStorage
        >>> storage = MemoryStorage(settings=settings)

    Note:
        This implementation includes performance optimizations:
        - Settings conversion caching
        - Parameter validation
        - Usage tracking for migration metrics
    """

    # Class-level tracking for migration metrics
    _legacy_init_count = 0
    _new_init_count = 0

    @overload
    def __init__(self, *, settings: Settings) -> None:
        """Initialize with settings object (new style)."""
        ...

    @overload
    def __init__(
        self,
        model_type: type[T],
        *,
        simulate_failures: bool = False,
        max_size_bytes: int | None = None,
        max_items: int | None = None,
    ) -> None:
        """Initialize with legacy parameters (deprecated)."""
        ...

    @validate_settings
    def __init__(self, model_type: type[T] | None = None, **kwargs: Any) -> None:
        """Initialize memory storage with backward compatibility.

        Supports both new-style initialization with settings object and
        legacy initialization with individual parameters.

        Args:
            model_type: Model type for legacy initialization (deprecated)
            **kwargs: Settings object or legacy parameters

        Raises:
            TypeError: If settings is not a Settings instance
            ValueError: If settings lacks storage configuration
        """
        self._warn_deprecation()

        if "settings" in kwargs:
            # New-style initialization
            MemoryStorage._new_init_count += 1
            logger.debug("Using new-style initialization with settings object")
            super().__init__(settings=kwargs["settings"])
        else:
            # Legacy initialization
            MemoryStorage._legacy_init_count += 1
            logger.debug("Using legacy initialization with individual parameters")
            settings = create_settings_from_legacy(
                max_size_bytes=kwargs.get("max_size_bytes"),
                max_items=kwargs.get("max_items"),
            )
            super().__init__(settings=settings)

        # Log initialization metrics
        logger.info(
            "Memory storage initialization stats - Legacy: %d, New: %d",
            self._legacy_init_count,
            self._new_init_count,
        )

    def _warn_deprecation(self) -> None:
        """Emit deprecation warning with migration instructions."""
        warnings.warn(
            "\nThis MemoryStorage implementation is deprecated and will be removed in "
            "version 2.0.0.\n"
            "Please migrate to src.core.storage.strategies.memory_storage.storage.MemoryStorage.\n"
            "See the class docstring for migration instructions.",
            DeprecationWarning,
            stacklevel=2,
        )
