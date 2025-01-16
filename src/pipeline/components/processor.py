"""Document processor component for advanced document processing operations.

This module provides the document processor component that handles various document
processing operations including:
- PII detection and redaction
- Document summarization
- Embedding generation
- Topic clustering

The processor integrates multiple specialized components (PII detector, summarizer,
embedding generator, topic clusterer) and orchestrates their operation in a
configurable pipeline.

Main Components:
    - DocumentProcessor: Core processor implementing document transformation logic
"""

# Standard library imports

# Local application imports
from src.embeddings.embedding_generator import EmbeddingGenerator
from src.models import ClusteringConfig
from src.pipeline.components.base import PipelineComponent
from src.pipeline.errors import (
    CleanupError,
    ClusteringError,
    EmbeddingError,
    PIIError,
    ProcessingError,
    SummaryError,
)
from src.utils.document_processing import DocumentProcessor as BaseDocProcessor
from src.utils.pii_detector import PIIDetector
from src.utils.summarizer.config.settings import SummarizerConfig
from src.utils.summarizer.core.processor import DocumentSummarizer
from src.utils.topic_clustering import TopicClusterer


# Re-export for test mocking
SummarizerProcessor = DocumentSummarizer


class DocumentProcessor(PipelineComponent):
    """Component for processing documents through various transformation steps.

    This class orchestrates multiple document processing operations including PII
    detection, summarization, embedding generation, and topic clustering. It manages
    the sequence of operations and handles errors at each step.

    Attributes:
        doc_processor (BaseDocProcessor): Base document processing utilities
        pii_detector (PIIDetector): PII detection and redaction
        summarizer (DocumentSummarizer): Document summarization
        embedding_generator (EmbeddingGenerator): Text embedding generation
        topic_clusterer (TopicClusterer): Document clustering by topic
        logger (logging.Logger): Component logger

    Examples:
        >>> processor = DocumentProcessor(config)
        >>> docs = [{"content": {"body": "Sample text"}}]
        >>> processed = processor.process(docs, detect_pii=True)
    """

    def __init__(self, *args, **kwargs):
        """Initialize document processor with all sub-components.

        Args:
            *args: Variable length argument list passed to parent class
            **kwargs: Arbitrary keyword arguments passed to parent class

        Raises:
            ProcessingError: If initialization of any sub-component fails
        """
        super().__init__(*args, **kwargs)

        self.logger.debug("Initializing document processor sub-components")

        # Initialize sub-components
        try:
            self.doc_processor = BaseDocProcessor(logger=self.logger)
            self.logger.debug("Initialized base document processor")
        except Exception as e:
            self.logger.error("Failed to initialize base document processor: %s", str(e))
            raise

        try:
            self.pii_detector = PIIDetector()
            self.logger.debug("Initialized PII detector")
        except Exception as e:
            self.logger.error("Failed to initialize PII detector: %s", str(e))
            raise

        try:
            # Initialize summarizer with default config
            summary_config = SummarizerConfig(
                model_name="t5-small",
                max_length=150,
                min_length=20,
                min_word_count=30,
                chunk_size=512,
                chunk_overlap=50,
                device="cpu",
            )
            self.logger.debug("Created summarizer config: %s", vars(summary_config))
            self.summarizer = SummarizerProcessor(summarizer_config=summary_config)
            self.logger.debug("Initialized summarizer")
        except Exception as e:
            self.logger.error("Failed to initialize summarizer: %s", str(e))
            raise

        try:
            self.embedding_generator = EmbeddingGenerator()
            self.logger.debug("Initialized embedding generator")
        except Exception as e:
            self.logger.error("Failed to initialize embedding generator: %s", str(e))
            raise

        try:
            self.topic_clusterer = TopicClusterer(
                cache_host=self.config.cache_host,
                cache_port=self.config.cache_port,
                cache_ttl=self.config.cache_ttl,
            )
            self.logger.debug(
                "Initialized topic clusterer with cache settings: host=%s, port=%s, ttl=%s",
                self.config.cache_host,
                self.config.cache_port,
                self.config.cache_ttl,
            )
        except Exception as e:
            self.logger.error("Failed to initialize topic clusterer: %s", str(e))
            raise

        self.logger.debug("All document processor sub-components initialized successfully")

    def _validate_document(self, doc: dict) -> bool:
        """Validate a document for processing.

        Args:
            doc: Document to validate

        Returns:
            bool: True if document is valid, False otherwise
        """
        if not doc:
            return False

        body = doc.get("content", {}).get("body", "")
        if not isinstance(body, str):
            return False

        body = body.strip()
        if not body:
            return False

        return True

    def process(
        self,
        documents: list[dict],
        detect_pii: bool = True,
        deduplicate: bool = True,
        summary_config: SummarizerConfig | None = None,
        cluster_config: ClusteringConfig | None = None,
        **kwargs,
    ) -> list[dict]:
        """Process documents through various transformation steps.

        This method orchestrates the document processing pipeline, applying each
        transformation step in sequence. Steps include:
        1. Deduplication (optional)
        2. PII detection (optional)
        3. Summarization
        4. Embedding generation
        5. Topic clustering

        Args:
            documents: List of documents to process
            detect_pii: Whether to detect and analyze PII in documents
            deduplicate: Whether to remove duplicate documents
            summary_config: Optional configuration for summarization
            cluster_config: Optional configuration for topic clustering
            **kwargs: Additional arguments passed to processing steps

        Returns:
            List[Dict]: Processed documents with added metadata, summaries,
                       embeddings, and cluster assignments

        Raises:
            ProcessingError: If there are errors during processing
            PIIError: If PII detection fails
            SummaryError: If summarization fails
            EmbeddingError: If embedding generation fails
            ClusteringError: If topic clustering fails
        """
        if not documents:
            self.logger.warning("No documents to process")
            return []

        # Validate and filter documents
        valid_docs = []
        for doc in documents:
            if self._validate_document(doc):
                valid_docs.append(doc)
            else:
                self.logger.debug("Skipping invalid document: %s", str(doc))

        if not valid_docs:
            self.logger.warning("No valid documents to process after filtering")
            return []

        documents = valid_docs
        self.logger.info("Processing %d valid documents", len(documents))

        try:
            # Process in batches
            doc_batches = self.doc_processor.batch_documents(documents, self.config.batch_size)
            processed_docs = []

            for i, batch in enumerate(doc_batches):
                self.logger.info("Processing batch %d/%d", i + 1, len(doc_batches))

                try:
                    # Deduplicate if requested
                    if deduplicate:
                        self.logger.info("Deduplicating documents")
                        self.logger.debug("Pre-deduplication batch size: %d", len(batch))
                        batch = self.doc_processor.deduplicate_documents(batch)
                        self.logger.debug("Post-deduplication batch size: %d", len(batch))

                    if not batch:
                        self.logger.info("Batch is empty after deduplication, skipping")
                        continue

                    # Detect PII if requested
                    if detect_pii:
                        try:
                            self.logger.info("Detecting PII")
                            self.logger.debug(
                                "Processing %d documents for PII detection", len(batch)
                            )
                            batch = [self.pii_detector.analyze_document(doc) for doc in batch]
                            self.logger.debug("PII detection completed for batch")
                        except Exception as e:
                            self.logger.error("PII detection failed: %s", str(e))
                            raise PIIError("Error detecting PII: %s", str(e)) from e

                    # Generate summaries
                    try:
                        self.logger.info("Generating summaries")
                        self.logger.debug(
                            "Processing %d documents for summarization with config: %s",
                            len(batch),
                            summary_config,
                        )
                        batch = self.summarizer.process_documents(batch, summary_config)
                        self.logger.debug("Summarization completed for batch")
                    except Exception as e:
                        self.logger.error("Summarization failed: %s", str(e))
                        raise SummaryError("Error generating summaries: %s", str(e)) from e

                    # Generate embeddings
                    self.logger.info("Generating embeddings")
                    self.logger.debug(
                        "Processing %d documents for embedding generation", len(batch)
                    )
                    valid_batch = []
                    for doc in batch:
                        try:
                            # Check document length
                            try:
                                text = doc["content"]["body"].strip()
                                self.logger.debug("Document content length: %d chars", len(text))
                                if len(text) > self.config.max_document_length:
                                    self.logger.warning(
                                        "Document too long (%d chars), truncating to %d",
                                        len(text),
                                        self.config.max_document_length,
                                    )
                                    doc["content"]["body"] = text[: self.config.max_document_length]
                            except KeyError as e:
                                self.logger.error("Document missing required field: %s", str(e))
                                raise EmbeddingError(
                                    f"Document missing required field: {e!s}"
                                ) from e

                            # Generate embedding with retries
                            for attempt in range(self.config.max_retries):
                                try:
                                    doc = self.embedding_generator.generate_embeddings([doc])[0]
                                    valid_batch.append(doc)
                                    break
                                except Exception as e:
                                    if attempt == self.config.max_retries - 1:
                                        self.logger.error(
                                            "Failed to generate embedding after %d attempts: %s",
                                            self.config.max_retries,
                                            str(e),
                                        )
                                        raise EmbeddingError(
                                            "Failed to generate embedding after %d attempts",
                                            self.config.max_retries,
                                        ) from e
                                    else:
                                        self.logger.warning(
                                            "Retry %d for embedding generation",
                                            attempt + 1,
                                        )
                        except EmbeddingError:
                            raise
                        except Exception as e:
                            raise EmbeddingError(
                                "Error processing document for embedding: %s",
                                str(e),
                            ) from e
                    batch = valid_batch

                    # Perform topic clustering
                    try:
                        self.logger.info("Performing topic clustering")
                        batch = self.topic_clusterer.cluster_documents(batch, cluster_config)
                    except Exception as e:
                        raise ClusteringError("Error clustering documents: %s", str(e)) from e

                    processed_docs.extend(batch)

                except (PIIError, SummaryError, EmbeddingError, ClusteringError) as e:
                    self.logger.error("Error processing batch %d: %s", i + 1, str(e))
                    continue

            return processed_docs

        except Exception as e:
            error_msg = "Error in document processing: %s"
            self.logger.error(error_msg, str(e))
            raise ProcessingError(error_msg % str(e)) from e

    def cleanup(self):
        """Clean up resources used by the processor and its sub-components.

        This method ensures proper cleanup of all resources including the summarizer
        and topic clusterer components.

        Raises:
            CleanupError: If there are issues during cleanup of any component
        """
        try:
            if hasattr(self, "summarizer"):
                self.summarizer.cleanup()
            if hasattr(self, "topic_clusterer"):
                self.topic_clusterer.cleanup()
        except Exception as e:
            error_msg = "Error during cleanup: %s"
            self.logger.error(error_msg, str(e))
            raise CleanupError(error_msg % str(e)) from e
