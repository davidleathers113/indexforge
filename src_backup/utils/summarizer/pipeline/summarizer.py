"""Summarization pipeline implementation for text processing.

This module provides the core summarization pipeline functionality using Hugging Face
transformers with configurable parameters and error handling. It includes:

1. Pipeline Management:
   - Transformer model initialization
   - Configuration validation
   - Error handling
   - Resource management

2. Text Processing:
   - Chunk-based processing
   - Text cleaning
   - Length validation
   - Format handling

3. Summarization Features:
   - Configurable length control
   - Temperature and sampling
   - Beam search
   - N-gram control

4. Quality Control:
   - Input validation
   - Output verification
   - Error tracking
   - Performance metrics

Usage:
    ```python
    from transformers import pipeline
    from src.utils.summarizer.pipeline.summarizer import SummarizationPipeline
    from src.utils.summarizer.config.settings import SummarizerConfig

    # Create pipeline
    model = pipeline("summarization", model="t5-small")
    config = SummarizerConfig(
        max_length=150,
        min_length=50,
        temperature=0.7
    )
    summarizer = SummarizationPipeline(model, config)

    # Generate summary
    result = summarizer.generate_summary(
        "Long text to summarize...",
        config
    )
    print(result["summary"])
    ```

Note:
    - Uses Hugging Face transformers
    - Handles long texts via chunking
    - Provides detailed metadata
    - Includes error recovery
"""

import logging
from typing import Any

from transformers import Pipeline

from ..config.settings import SummarizerConfig
from ...text_processing import chunk_text_by_words, clean_text


logger = logging.getLogger(__name__)


class SummarizationError(Exception):
    """Base class for summarization-specific errors."""

    pass


class ValidationError(Exception):
    """Validation error for summarizer parameters."""

    pass


class SummarizationPipeline:
    """Pipeline for text summarization."""

    def __init__(
        self,
        pipeline: Pipeline,
        config: SummarizerConfig | None = None,
    ) -> None:
        """Initialize the summarization pipeline.

        Args:
            pipeline: Hugging Face pipeline instance
            config: Optional summarization configuration
        """
        self.pipeline = pipeline
        self.config = config or SummarizerConfig()

    def _validate_config(self) -> None:
        """Validate the configuration settings.

        Raises:
            ValidationError: If any configuration parameters are invalid
        """
        if self.config.max_length < self.config.min_length:
            raise ValidationError("max_length must be greater than min_length")
        if self.config.min_length < 1:
            raise ValidationError("min_length must be at least 1")
        if self.config.temperature < 0 or self.config.temperature > 1:
            raise ValidationError("temperature must be between 0 and 1")
        if self.config.top_p < 0 or self.config.top_p > 1:
            raise ValidationError("top_p must be between 0 and 1")
        if self.config.chunk_size < 1:
            raise ValidationError("chunk_size must be at least 1")
        if self.config.chunk_overlap < 0:
            raise ValidationError("chunk_overlap must be non-negative")

        # Ensure min_word_count exists and is valid
        min_word_count = getattr(self.config, "min_word_count", 100)
        if min_word_count < 1:
            raise ValidationError("min_word_count must be at least 1")
        if not hasattr(self.config, "min_word_count"):
            self.config.min_word_count = min_word_count

    def generate_summary(
        self, text: str, config: SummarizerConfig | None = None
    ) -> dict[str, Any]:
        """Generate a summary for the given text.

        Args:
            text: Text to summarize
            config: Optional summary configuration

        Returns:
            Dict containing status, summary, and metadata
        """
        if not text:
            return {"status": "error", "error": "Empty text"}

        if config:
            self.config = config

        try:
            self._validate_config()

            # Clean and truncate text
            text = clean_text(text)
            word_count = len(text.split())

            if word_count < self.config.min_word_count:
                return {
                    "status": "success",
                    "summary": text,
                    "metadata": {
                        "original_length": word_count,
                        "was_summarized": False,
                        "reason": "Text too short",
                    },
                }

            # Split text into chunks
            chunks = chunk_text_by_words(
                text, self.config.chunk_size, overlap=self.config.chunk_overlap
            )

            # Process each chunk with error handling
            chunk_summaries = []
            failed_chunks = 0

            for i, chunk in enumerate(chunks):
                try:
                    summary = self._summarize_chunk(chunk)
                    if summary.strip():  # Only add non-empty summaries
                        chunk_summaries.append(summary)
                except Exception as e:
                    failed_chunks += 1
                    logger.error(f"Error processing chunk {i}: {e!s}")
                    continue

            if not chunk_summaries:
                if failed_chunks == len(chunks):
                    return {"status": "error", "error": "All chunks failed to summarize"}
                return {
                    "status": "error",
                    "error": "No valid summaries generated",
                    "metadata": {"failed_chunks": failed_chunks},
                }

            # Combine chunk summaries
            final_summary = self._combine_summaries(chunk_summaries)

            return {
                "status": "success",
                "summary": final_summary,
                "metadata": {
                    "original_length": word_count,
                    "summary_length": len(final_summary.split()),
                    "compression_ratio": len(final_summary.split()) / word_count,
                    "chunks_processed": len(chunks),
                    "failed_chunks": failed_chunks,
                    "was_summarized": True,
                },
            }

        except ValidationError as e:
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.error(f"Error generating summary: {e!s}")
            return {"status": "error", "error": str(e)}

    def _summarize_chunk(self, text: str) -> str:
        """Summarize a single chunk of text.

        Args:
            text: Text chunk to summarize

        Returns:
            Summarized text
        """
        try:
            result = self.pipeline(
                text[:1024],  # Simple truncation of input text
                max_length=self.config.max_length,
                min_length=self.config.min_length,
                do_sample=True,  # Enable sampling for temperature and top_p to work
                temperature=self.config.temperature,
                top_p=self.config.top_p,
            )
            return result[0]["summary_text"].strip()
        except Exception as e:
            logger.error(f"Error in summarization: {e!s}")
            raise SummarizationError(f"Failed to summarize chunk: {e!s}")

    def _combine_summaries(self, summaries: list[str]) -> str:
        """Combine multiple summaries into one.

        Args:
            summaries: List of summaries to combine

        Returns:
            Combined summary
        """
        if len(summaries) == 1:
            return summaries[0]

        combined_text = " ".join(summaries)
        return self._summarize_chunk(combined_text)
