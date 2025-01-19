"""Base processor for ML pipeline components.

This module defines the base processor class that all pipeline components should inherit from.
It provides configuration management, validation, and common utilities.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .config.settings import PipelineConfig, ProcessingConfig


class BaseProcessor(ABC):
    """Base class for all pipeline processors.

    This class provides common functionality for configuration management,
    validation, and resource handling. All pipeline processors should inherit
    from this class.
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        processing_config: Optional[ProcessingConfig] = None,
    ) -> None:
        """Initialize the processor.

        Args:
            config: Optional pipeline configuration. If not provided, default config is used.
            processing_config: Optional processing-specific configuration. If provided,
                overrides the processing settings in the main config.
        """
        self.config = config or PipelineConfig()
        self.processing_config = processing_config or self.config.processing
        self._validate_config()
        self._initialized = False

    def _validate_config(self) -> None:
        """Validate the processor configuration.

        This method performs additional validation beyond the basic Pydantic validation.
        Subclasses can override this to add specific validation rules.

        Raises:
            ValueError: If the configuration is invalid
        """
        if not isinstance(self.processing_config, ProcessingConfig):
            raise ValueError("processing_config must be an instance of ProcessingConfig")

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the processor.

        This method should be called before processing any data. It handles
        resource allocation, connection setup, and other initialization tasks.

        Raises:
            RuntimeError: If initialization fails
        """
        self._initialized = True

    @abstractmethod
    def process(self, data: Any) -> Dict[str, Any]:
        """Process the input data.

        Args:
            data: The input data to process

        Returns:
            Dict containing the processing results

        Raises:
            RuntimeError: If the processor is not initialized
            ValueError: If the input data is invalid
        """
        if not self._initialized:
            raise RuntimeError("Processor must be initialized before processing")
        return {}

    def cleanup(self) -> None:
        """Clean up resources used by the processor.

        This method handles resource cleanup, connection closing, and other
        cleanup tasks. Subclasses should override this to add specific cleanup logic.
        """
        self._initialized = False

    def __enter__(self) -> "BaseProcessor":
        """Context manager entry.

        Returns:
            self: The processor instance
        """
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        self.cleanup()

    @property
    def is_initialized(self) -> bool:
        """Check if the processor is initialized.

        Returns:
            bool: True if initialized, False otherwise
        """
        return self._initialized
