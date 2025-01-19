"""Document summarization utilities for content compression.

This module provides document summarization capabilities using transformer-based
models with caching and batch processing support. It includes:

1. Text Summarization:
   - Transformer-based models
   - Configurable parameters
   - Length control
   - Quality settings

2. Document Processing:
   - Batch processing
   - Chunk handling
   - Metadata generation
   - Error handling

3. Performance Optimization:
   - Redis-based caching
   - Retry mechanism
   - Resource cleanup
   - Memory management

4. Quality Control:
   - Compression ratio tracking
   - Model selection
   - Parameter tuning
   - Error tracking

Usage:
    ```python
    from src.utils.summarizer import DocumentSummarizer
    from src.models.settings import SummarizerConfig

    summarizer = DocumentSummarizer(
        model_name="facebook/bart-large-cnn",
        device=-1,  # CPU
        batch_size=4
    )

    # Process single document
    config = SummarizerConfig(
        max_length=150,
        min_length=50,
        do_sample=False
    )
    result = summarizer.generate_summary(text, config)

    # Process batch of documents
    processed_docs = summarizer.process_documents(documents, config)
    ```

Note:
    - Uses Hugging Face transformers
    - Supports multiple models
    - Caches results for performance
    - Handles large documents
"""

from functools import wraps
import logging

from transformers import pipeline

from src.models.settings import SummarizerConfig
from src.utils.cache_manager import CacheManager, cached_with_retry
from src.utils.text_processing import chunk_text_by_words, clean_text, truncate_text


logger = logging.getLogger(__name__)


def setup_caching(func):
    """Setup caching for instance methods.

    This decorator configures caching for class methods using the instance's
    cache manager. It ensures that caching is set up only once per method
    and reused for subsequent calls.

    Args:
        func: The method to be cached

    Returns:
        Wrapped method with caching support
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, "_cached_func"):
            self._cached_func = cached_with_retry(
                cache_manager=self.cache_manager,
                key_prefix="summary",
                max_attempts=3,
            )(func)
        return self._cached_func(self, *args, **kwargs)

    return wrapper


class DocumentSummarizer:
    def __init__(
        self,
        model_name: str = "facebook/bart-large-cnn",
        device: int = -1,  # CPU
        batch_size: int = 4,
        cache_manager: CacheManager = None,
        cache_host: str = "localhost",
        cache_port: int = 6379,
        cache_ttl: int = 86400,  # 24 hours
    ):
        self.summarizer = pipeline(
            task="summarization",
            model=model_name,
            device=device,
        )
        self.batch_size = batch_size
        self.model_name = model_name

        # Use provided cache_manager or create a new one
        self.cache_manager = cache_manager or CacheManager(
            host=cache_host,
            port=cache_port,
            prefix="sum",
            default_ttl=cache_ttl,
        )
        self.logger = logging.getLogger(__name__)

    @setup_caching
    def _summarize_chunk(self, text: str, config: SummarizerConfig) -> str:
        """Summarize a single chunk of text."""
        try:
            # Clean and truncate text if needed
            text = clean_text(text)
            text = truncate_text(text, config.max_length * 4, use_tokens=False)

            summary = self.summarizer(
                text,
                max_length=config.max_length,
                min_length=config.min_length,
                do_sample=config.do_sample,
                temperature=config.temperature,
                top_p=config.top_p,
            )[0]["summary_text"]

            return summary.strip()
        except Exception as e:
            self.logger.error(f"Error summarizing chunk: {e!s}")
            raise  # Re-raise to be handled by caller

    def _combine_summaries(self, summaries: list[str], config: SummarizerConfig) -> str:
        """Combine multiple summaries into one."""
        if not summaries:
            return ""

        if len(summaries) == 1:
            return truncate_text(summaries[0], config.max_length, use_tokens=False)

        # Combine summaries with separators
        combined = " ".join(summaries)

        # Create a new config with the same max_length for the final summary
        final_config = SummarizerConfig(
            max_length=config.max_length,
            min_length=config.min_length,
            do_sample=config.do_sample,
            temperature=config.temperature,
            top_p=config.top_p,
        )

        # Generate a final summary of the combined text
        final_summary = self._summarize_chunk(combined, final_config)

        # Ensure the final summary respects max_length
        return truncate_text(final_summary, config.max_length, use_tokens=False)

    def generate_summary(self, text: str, config: SummarizerConfig = None) -> dict:
        """Generate a summary for the given text.

        Args:
            text: Text to summarize
            config: Optional summary configuration

        Returns:
            Dict containing status and summary/error
        """
        if not text:
            return {"status": "error", "error": "Empty text"}

        if not config:
            config = SummarizerConfig()

        try:
            # Split text into chunks
            chunks = chunk_text_by_words(text, config.chunk_size)
            chunk_summaries = []

            # Process each chunk
            for chunk in chunks:
                try:
                    summary = self._summarize_chunk(chunk, config)
                    chunk_summaries.append(summary)
                except Exception as e:
                    self.logger.error(f"Error processing chunk: {e!s}")
                    # Continue with other chunks even if one fails
                    continue

            if not chunk_summaries:
                return {"status": "error", "error": "All chunks failed to summarize"}

            # Combine chunk summaries
            final_summary = self._combine_summaries(chunk_summaries, config)
            return {"status": "success", "summary": final_summary}

        except Exception as e:
            self.logger.error(f"Error generating summary: {e!s}")
            return {"status": "error", "error": str(e)}

    def process_documents(
        self,
        documents: list[dict],
        config: SummarizerConfig = None,
    ) -> list[dict]:
        """Process a batch of documents.

        Args:
            documents: List of documents to process
            config: Optional summary configuration

        Returns:
            List of processed documents
        """
        if not documents:
            return []

        if not config:
            config = SummarizerConfig()

        processed_docs = []
        for doc in documents:
            try:
                # Get text content
                text = doc.get("content", {}).get("body", "")
                if not text:
                    continue

                # Generate summary
                result = self.generate_summary(text, config)

                # Create processed document
                processed_doc = doc.copy()
                if result["status"] == "success":
                    processed_doc["content"]["summary"] = result["summary"]
                    # Calculate compression ratio
                    compression_ratio = len(result["summary"]) / len(text)
                    processed_doc.setdefault("metadata", {})["summarization"] = {
                        "compression_ratio": compression_ratio,
                        "model": self.model_name,
                    }
                else:
                    processed_doc["content"]["summary"] = None
                    processed_doc.setdefault("metadata", {})["summarization"] = {
                        "error": result["error"],
                        "model": self.model_name,
                    }

                processed_docs.append(processed_doc)

            except Exception as e:
                self.logger.error(f"Error processing document: {e!s}")
                # Add document with error info
                processed_doc = doc.copy()
                processed_doc["content"]["summary"] = None
                processed_doc.setdefault("metadata", {})["summarization"] = {
                    "error": str(e),
                    "model": self.model_name,
                }
                processed_docs.append(processed_doc)

        return processed_docs

    def cleanup(self):
        """Clean up resources."""
        try:
            # Clean up summarizer pipeline
            if hasattr(self, "summarizer"):
                del self.summarizer
        except Exception:
            logger.error("Error cleaning up summarizer", exc_info=True)
            raise
