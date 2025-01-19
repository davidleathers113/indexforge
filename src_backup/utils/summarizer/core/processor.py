"""Document processing implementation for text summarization.

This module provides the core document processing functionality for text summarization,
including resource management, caching, and batch processing. It includes:

1. Document Processing:
   - Single and batch document processing
   - Resource management with context managers
   - Automatic cleanup of model resources
   - Error handling and recovery

2. Pipeline Management:
   - Lazy initialization of summarization pipeline
   - Model resource cleanup
   - Device management (CPU/GPU)
   - Pipeline configuration

3. Caching Support:
   - Redis-based caching
   - Cache key management
   - TTL configuration
   - Error recovery

4. Performance Features:
   - Batch processing optimization
   - Resource cleanup
   - Memory management
   - Error tracking

Usage:
    ```python
    from src.utils.summarizer.core.processor import DocumentSummarizer
    from src.utils.summarizer.config.settings import SummarizerConfig

    # Initialize with custom config
    config = SummarizerConfig(
        model_name="t5-small",
        max_length=150,
        min_length=50
    )
    summarizer = DocumentSummarizer(config)

    # Process single document
    doc = {"content": {"body": "Long text to summarize..."}}
    processed = summarizer._process_single_document(doc)

    # Process batch of documents
    docs = [doc1, doc2, doc3]
    processed_batch = summarizer.process_documents(docs)
    ```

Note:
    - Handles resource cleanup automatically
    - Supports both cached and non-cached processing
    - Manages model resources efficiently
    - Provides detailed error tracking
"""

from collections.abc import Iterator
from contextlib import contextmanager
import logging
from typing import Any

from transformers import pipeline

from ..caching.decorators import with_cache
from ..config.settings import CacheConfig, SummarizerConfig
from ..pipeline.summarizer import SummarizationPipeline


logger = logging.getLogger(__name__)


class DocumentSummarizer:
    """Main document processing class."""

    def __init__(
        self,
        summarizer_config: SummarizerConfig | None = None,
        cache_config: CacheConfig | None = None,
        cache_manager: Any | None = None,
    ) -> None:
        """Initialize the document processor.

        Args:
            summarizer_config: Configuration for summarization
            cache_config: Configuration for caching
            cache_manager: Optional cache manager instance
        """
        self.summarizer_config = summarizer_config or SummarizerConfig()
        logger.info(f"Initialized with config: {vars(self.summarizer_config)}")
        self.cache_config = cache_config
        self.cache_manager = cache_manager

        # Initialize the pipeline
        self._pipeline = None
        self._summarizer = None

    def cleanup(self):
        """Clean up resources."""
        try:
            if self._pipeline is not None:
                del self._pipeline
            if self._summarizer is not None:
                del self._summarizer
        except Exception:  # Log the error and re-raise
            logger.error("Error cleaning up summarizer", exc_info=True)
            raise

    @property
    def summarizer(self) -> SummarizationPipeline:
        """Get or create the summarization pipeline.

        Returns:
            Initialized summarization pipeline
        """
        if self._summarizer is None:
            if self._pipeline is None:
                self._pipeline = pipeline(
                    task="summarization",
                    model=self.summarizer_config.model_name,
                    device=self.summarizer_config.device,
                )
            self._summarizer = SummarizationPipeline(
                pipeline=self._pipeline,
                config=self.summarizer_config,
            )
        return self._summarizer

    @contextmanager
    def _resource_cleanup(self) -> Iterator[None]:
        """Context manager for resource cleanup."""
        try:
            yield
        finally:
            if self._pipeline is not None:
                del self._pipeline
                self._pipeline = None
            if self._summarizer is not None:
                self._summarizer = None

    def process_documents(
        self, documents: list[dict], summary_config: SummarizerConfig | None = None
    ) -> list[dict]:
        """Process a batch of documents.

        Args:
            documents: List of documents to process
            summary_config: Optional summary configuration

        Returns:
            List of processed documents
        """
        if not documents:
            logger.warning("No documents to process")
            return []

        # Use provided config or default
        config = summary_config or self.summarizer_config
        logger.info(f"Using config for processing: {vars(config)}")

        processed_docs = []
        for doc in documents:
            try:
                text = doc["content"]["body"].strip()
                word_count = len(text.split())

                # Debug logging
                logger.debug(f"Document word count: {word_count}")
                logger.debug(f"Config min_word_count: {getattr(config, 'min_word_count', None)}")
                logger.debug(f"Config attributes: {vars(config)}")

                # Skip if text is too short
                min_words = getattr(config, "min_word_count", 100)  # Default to 100 if not set
                if word_count < min_words:
                    doc["summary"] = text
                    doc["summary_status"] = "success"
                    processed_docs.append(doc)
                    continue

                # Generate summary
                result = self.summarizer.generate_summary(text, config)

                if result["status"] == "success":
                    doc["summary"] = result["summary"]
                    doc["summary_status"] = "success"
                else:
                    doc["summary"] = text
                    doc["summary_status"] = "error"
                    doc["summary_error"] = result.get("error", "Unknown error")
                    logger.error(f"Error summarizing document: {result.get('error')}")

                processed_docs.append(doc)

            except Exception as e:
                logger.error(f"Error processing document: {e!s}")
                doc["summary"] = doc["content"]["body"]
                doc["summary_status"] = "error"
                doc["summary_error"] = str(e)
                processed_docs.append(doc)

        return processed_docs

    def _process_single_document(
        self,
        document: dict[str, Any],
    ) -> dict[str, Any]:
        """Process a single document.

        Args:
            document: Document to process

        Returns:
            Processed document with summary
        """
        if self.cache_manager:
            return self._process_single_document_with_cache(document)
        return self._process_single_document_without_cache(document)

    @with_cache(key_prefix="doc_sum")
    def _process_single_document_with_cache(
        self,
        document: dict[str, Any],
    ) -> dict[str, Any]:
        """Process a single document with caching.

        Args:
            document: Document to process

        Returns:
            Processed document with summary
        """
        return self._process_single_document_without_cache(document)

    def _process_single_document_without_cache(
        self,
        document: dict[str, Any],
    ) -> dict[str, Any]:
        """Process a single document without caching.

        Args:
            document: Document to process

        Returns:
            Processed document with summary
        """
        # Get text content
        content = document.get("content", {})
        text = content.get("body", "")
        if not text:
            return document

        # Generate summary
        result = self.summarizer.generate_summary(text)

        # Create processed document
        processed_doc = document.copy()
        processed_doc["content"] = content.copy()

        if result["status"] == "success":
            processed_doc["content"]["summary"] = result["summary"]
            processed_doc.setdefault("metadata", {})["summarization"] = {
                "compression_ratio": result["compression_ratio"],
                "model": self.summarizer_config.model_name,
            }
        else:
            processed_doc["content"]["summary"] = None
            processed_doc.setdefault("metadata", {})["summarization"] = {
                "error": result["error"],
                "model": self.summarizer_config.model_name,
            }

        return processed_doc
