"""Base pipeline component module providing core abstractions for document processing.

This module defines the base interfaces and abstractions for pipeline components
in the document processing system. It provides a common foundation that ensures
all pipeline components follow the same contract and can be composed together.

Main Components:
    - PipelineComponent: Abstract base class for all pipeline components
"""

from abc import ABC, abstractmethod
import logging
from typing import Dict, List, Optional

from src.pipeline.config.settings import PipelineConfig


class PipelineComponent(ABC):
    """Abstract base class for all pipeline components.

    This class defines the interface that all pipeline components must implement.
    It provides common functionality for configuration and logging, while requiring
    subclasses to implement specific processing logic.

    Attributes:
        config (PipelineConfig): Configuration settings for the component
        logger (logging.Logger): Logger instance for tracking operations

    Examples:
        >>> class MyComponent(PipelineComponent):
        ...     def process(self, documents, **kwargs):
        ...         return [self._process_doc(doc) for doc in documents]
    """

    def __init__(self, config: PipelineConfig, logger: Optional[logging.Logger] = None):
        """Initialize pipeline component.

        Args:
            config: Pipeline configuration settings
            logger: Optional logger instance. If not provided, creates a new logger
                   with the class name.
        """
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def process(self, documents: List[Dict], **kwargs) -> List[Dict]:
        """Process documents through this pipeline component.

        This method must be implemented by all subclasses to define their specific
        document processing logic.

        Args:
            documents: List of documents to process, where each document is a dictionary
                      containing content and metadata
            **kwargs: Additional keyword arguments for processing customization

        Returns:
            List[Dict]: Processed documents with potentially modified content and metadata

        Raises:
            NotImplementedError: If the subclass doesn't implement this method
        """
        pass

    def cleanup(self):
        """Clean up component resources.

        This method should be overridden by subclasses that need to perform cleanup
        operations (e.g., closing connections, freeing resources) when the pipeline
        is done processing.
        """
        pass
