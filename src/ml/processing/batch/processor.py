"""Batch document processor implementation.

This module provides functionality for processing batches of documents efficiently,
with support for concurrent processing, resource management, and error handling.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from src.core.models.documents import ProcessingStep
from src.ml.processing.document.base import BaseDocumentProcessor, ProcessingResult
from src.ml.processing.document.config import DocumentProcessingConfig
from src.ml.processing.document.errors import DocumentProcessingError, DocumentValidationError


class BatchProcessor:
    """Processor for handling document batches efficiently.

    Provides functionality for:
    - Concurrent document processing
    - Resource management
    - Error handling and recovery
    - Progress tracking
    - Performance monitoring

    Attributes:
        config: Document processing configuration
        logger: Logger instance
    """

    def __init__(
        self,
        processor_class: Type[BaseDocumentProcessor],
        config: Optional[DocumentProcessingConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the batch processor.

        Args:
            processor_class: Document processor class to use
            config: Optional document processing configuration
            logger: Optional logger instance
        """
        self.config = config or DocumentProcessingConfig()
        self.logger = logger or logging.getLogger(__name__)
        self._processor_class = processor_class
        self._processors: List[BaseDocumentProcessor] = []
        self._results: Dict[str, ProcessingResult] = {}
        self._metadata: Dict[str, Any] = {}

    async def process_batch(
        self,
        files: List[Path],
        max_concurrent: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, ProcessingResult]:
        """Process a batch of documents concurrently.

        Args:
            files: List of document files to process
            max_concurrent: Maximum number of concurrent processors
            metadata: Optional processing metadata

        Returns:
            Dictionary mapping file paths to processing results

        Raises:
            DocumentProcessingError: If batch processing fails
        """
        try:
            # Initialize processors
            self._initialize_processors(max_concurrent)
            self._results.clear()
            self._metadata = metadata or {}

            # Create processing tasks
            tasks = []
            semaphore = asyncio.Semaphore(max_concurrent)

            for file_path in files:
                task = self._process_file(file_path, semaphore)
                tasks.append(task)

            # Process files concurrently
            await asyncio.gather(*tasks)

            return self._results.copy()

        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            raise DocumentProcessingError(f"Batch processing failed: {e}") from e

        finally:
            # Clean up processors
            self._cleanup_processors()

    def get_processing_steps(self) -> List[ProcessingStep]:
        """Get processing steps for the batch.

        Returns:
            List of processing steps
        """
        if not self._processors:
            return []
        return self._processors[0].get_processing_steps()

    def _initialize_processors(self, count: int) -> None:
        """Initialize document processors.

        Args:
            count: Number of processors to initialize
        """
        self._processors = []
        for _ in range(count):
            processor = self._processor_class(config=self.config)
            processor.initialize()
            self._processors.append(processor)

    def _cleanup_processors(self) -> None:
        """Clean up all processors."""
        for processor in self._processors:
            try:
                processor.cleanup()
            except Exception as e:
                self.logger.warning(f"Error cleaning up processor: {e}")
        self._processors.clear()

    async def _process_file(self, file_path: Path, semaphore: asyncio.Semaphore) -> None:
        """Process a single file using an available processor.

        Args:
            file_path: Path to document file
            semaphore: Semaphore for controlling concurrency
        """
        async with semaphore:
            try:
                # Get available processor
                processor = self._get_available_processor()
                if not processor:
                    raise DocumentProcessingError("No available processors")

                # Process file
                result = processor.process(file_path)
                self._results[str(file_path)] = result

                # Update metadata
                if result.status == "success":
                    self.logger.info(f"Successfully processed {file_path}")
                else:
                    self.logger.warning(
                        f"Processing {file_path} completed with errors: {result.errors}"
                    )

            except DocumentValidationError as e:
                self.logger.error(f"Validation error for {file_path}: {e}")
                self._results[str(file_path)] = ProcessingResult(
                    status="error", errors=[f"Validation error: {e}"]
                )

            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {e}")
                self._results[str(file_path)] = ProcessingResult(
                    status="error", errors=[f"Processing error: {e}"]
                )

    def _get_available_processor(self) -> Optional[BaseDocumentProcessor]:
        """Get an available processor from the pool.

        Returns:
            Available processor or None if none available
        """
        for processor in self._processors:
            if processor.is_initialized:
                return processor
        return None
