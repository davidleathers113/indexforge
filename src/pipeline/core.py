"""Core pipeline implementation for document processing and indexing.

This module implements the main pipeline orchestrator that handles document processing,
including loading, processing, and indexing of documents. It provides a flexible
pipeline that can be configured to run specific steps and handles various document
operations like PII detection, summarization, embedding generation, and clustering.

Classes:
    Pipeline: Main orchestrator class that manages the document processing pipeline.

Example:
    ```python
    pipeline = Pipeline(
        export_dir="path/to/exports",
        index_url="http://localhost:8080",
        debug=True
    )

    # Process documents with all default steps
    documents = pipeline.process_documents()

    # Process with specific steps and configurations
    from .steps import PipelineStep
    documents = pipeline.process_documents(
        steps={PipelineStep.LOAD, PipelineStep.SUMMARIZE},
        detect_pii=True,
        deduplicate=True
    )
    ```
"""

import logging
import os
from typing import Dict, List, Optional, Set

# Set tokenizers parallelism to avoid deadlock warnings
if "TOKENIZERS_PARALLELISM" not in os.environ:
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

from src.configuration.logger_setup import setup_json_logger
from src.connectors.notion_connector import NotionConnector
from src.models import ClusteringConfig
from src.utils.embedding_generator import EmbeddingGenerator
from src.utils.pii_detector import PIIDetector as _PIIDetector
from src.utils.summarizer import DocumentSummarizer
from src.utils.summarizer.config.settings import SummarizerConfig
from src.utils.topic_clustering import TopicClusterer
from src.utils.vector_index import VectorIndex

from .components.indexer import DocumentIndexer
from .components.loader import DocumentLoader
from .components.processor import DocumentProcessor
from .config.settings import PipelineConfig
from .document_ops import DocumentOperations
from .errors import DirectoryError, PipelineError
from .search import SearchOperations
from .steps import PipelineStep

# Re-export for test mocking
PIIDetector = _PIIDetector

# Re-export for test mocking
__all__ = [
    "Pipeline",
    "DocumentSummarizer",
    "EmbeddingGenerator",
    "TopicClusterer",
    "VectorIndex",
]


class Pipeline:
    """Main pipeline orchestrator for document processing and indexing.

    This class orchestrates the entire document processing pipeline, managing the flow
    of documents through various processing stages including loading, processing,
    and indexing. It provides flexible configuration options and can be customized
    to run specific pipeline steps.

    The pipeline supports the following main operations:
    - Document loading from Notion exports
    - PII detection and handling
    - Document summarization
    - Embedding generation
    - Topic clustering
    - Vector indexing
    - Document deduplication

    Attributes:
        config (PipelineConfig): Configuration settings for the pipeline
        logger (logging.Logger): Logger instance for pipeline operations
        notion (NotionConnector): Connector for Notion exports
        loader (DocumentLoader): Component for loading documents
        processor (DocumentProcessor): Component for document processing
        indexer (DocumentIndexer): Component for document indexing
        pii_detector (PIIDetector): Component for PII detection
        doc_ops (DocumentOperations): Document-related operations
        search_ops (SearchOperations): Search-related operations
        processed_files (Set[str]): Set of processed file paths
        failed_files (Dict[str, str]): Mapping of failed files to error messages

    Example:
        ```python
        pipeline = Pipeline(
            export_dir="exports",
            index_url="http://localhost:8080",
            batch_size=100
        )

        # Process documents with default settings
        documents = pipeline.process_documents()

        # Search indexed documents
        results = pipeline.search("query text")
        ```
    """

    def __init__(
        self,
        export_dir: str,
        index_url: str = "http://localhost:8080",
        log_dir: str = "logs",
        batch_size: int = 100,
        class_name: str = "Document",
        cache_host: Optional[str] = "localhost",
        cache_port: Optional[int] = 6379,
        cache_ttl: Optional[int] = 86400,
        debug: bool = False,
    ):
        """Initialize the pipeline with the specified configuration.

        This constructor sets up all necessary components for the document processing
        pipeline, including the document loader, processor, indexer, and various
        operations handlers. It also initializes logging and validates the export
        directory.

        Args:
            export_dir (str): Path to the directory containing exported documents
            index_url (str, optional): URL of the vector index service. Defaults to "http://localhost:8080"
            log_dir (str, optional): Directory for storing log files. Defaults to "logs"
            batch_size (int, optional): Number of documents to process in each batch. Defaults to 100
            class_name (str, optional): Name of the document class in the vector index. Defaults to "Document"
            cache_host (str, optional): Redis cache host address. Defaults to "localhost"
            cache_port (int, optional): Redis cache port number. Defaults to 6379
            cache_ttl (int, optional): Cache TTL in seconds. Defaults to 86400 (24 hours)
            debug (bool, optional): Enable debug logging. Defaults to False

        Raises:
            DirectoryError: If export_dir doesn't exist or isn't a directory
            PipelineError: If any component initialization fails
        """
        try:
            # Create and validate configuration
            self.config = PipelineConfig(
                export_dir=export_dir,
                index_url=index_url,
                log_dir=log_dir,
                batch_size=batch_size,
                class_name=class_name,
                cache_host=cache_host or "localhost",
                cache_port=cache_port or 6379,
                cache_ttl=cache_ttl or 86400,
            )

            # Validate export directory
            if not self.config.export_dir.exists():
                raise DirectoryError(f"Export directory does not exist: {export_dir}")
            if not self.config.export_dir.is_dir():
                raise DirectoryError(f"Export path is not a directory: {export_dir}")

            # Setup logging
            os.makedirs(self.config.log_dir, exist_ok=True)
            self.logger = setup_json_logger(
                name=__name__,
                log_path=os.path.join(self.config.log_dir, "pipeline.json"),
                level=logging.DEBUG if debug else logging.INFO,
            )
            self.logger.info("Initializing pipeline with config: %s", vars(self.config))

            # Initialize pipeline components
            self.logger.debug("Initializing pipeline components")
            try:
                self.notion = NotionConnector(self.config.export_dir)
                self.logger.debug("Notion connector initialized")

                self.loader = DocumentLoader(
                    notion_connector=self.notion, config=self.config, logger=self.logger
                )
                self.logger.debug("Document loader initialized")
            except Exception as e:
                self.logger.error("Failed to initialize document loader: %s", str(e))
                raise

            try:
                self.processor = DocumentProcessor(config=self.config, logger=self.logger)
                self.logger.debug("Document processor initialized")
            except Exception as e:
                self.logger.error("Failed to initialize document processor: %s", str(e))
                raise

            try:
                self.indexer = DocumentIndexer(config=self.config, logger=self.logger)
                self.logger.debug("Document indexer initialized")
            except Exception as e:
                self.logger.error("Failed to initialize document indexer: %s", str(e))
                raise

            try:
                self.pii_detector = PIIDetector()
                self.logger.debug("PII detector initialized")
            except Exception as e:
                self.logger.error("Failed to initialize PII detector: %s", str(e))
                raise

            # Initialize operations with required instances
            self.logger.debug("Initializing pipeline operations")
            try:
                self.doc_ops = DocumentOperations(
                    summarizer=self.processor.summarizer,
                    embedding_generator=self.processor.embedding_generator,
                    vector_index=self.indexer.vector_index,
                    logger=self.logger,
                )
                self.logger.debug("Document operations initialized")
            except Exception as e:
                self.logger.error("Failed to initialize document operations: %s", str(e))
                raise

            try:
                self.search_ops = SearchOperations(
                    embedding_generator=self.processor.embedding_generator,
                    vector_index=self.indexer.vector_index,
                    topic_clusterer=self.processor.topic_clusterer,
                    logger=self.logger,
                )
                self.logger.debug("Search operations initialized")
            except Exception as e:
                self.logger.error("Failed to initialize search operations: %s", str(e))
                raise

            # Track processed files and errors
            self.processed_files: Set[str] = set()
            self.failed_files: Dict[str, str] = {}  # file_path -> error_message
            self.logger.info("Pipeline initialized successfully")

        except Exception as e:
            error_msg = f"Failed to initialize pipeline: {str(e)}"
            if hasattr(self, "logger"):
                self.logger.error(error_msg, exc_info=True)
            raise PipelineError(error_msg) from e

    def process_documents(
        self,
        steps: Optional[Set[PipelineStep]] = None,
        summary_config: Optional[SummarizerConfig] = None,
        cluster_config: Optional[ClusteringConfig] = None,
        detect_pii: bool = True,
        deduplicate: bool = True,
    ) -> List[Dict]:
        """Process documents through the specified pipeline steps.

        This method orchestrates the document processing workflow, executing the
        specified steps in sequence. If no steps are specified, all available steps
        will be executed. The method supports flexible configuration of summarization,
        clustering, PII detection, and deduplication.

        Args:
            steps (Set[PipelineStep], optional): Set of pipeline steps to execute.
                If None, all steps will be executed. Defaults to None
            summary_config (SummarizerConfig, optional): Configuration for document
                summarization. Only used if SUMMARIZE step is included. Defaults to None
            cluster_config (ClusteringConfig, optional): Configuration for topic
                clustering. Only used if CLUSTER step is included. Defaults to None
            detect_pii (bool, optional): Whether to detect PII in documents.
                Only used if PII step is included. Defaults to True
            deduplicate (bool, optional): Whether to deduplicate documents.
                Only used if DEDUPLICATE step is included. Defaults to True

        Returns:
            List[Dict]: List of processed documents, where each document is a
                dictionary containing the document content and metadata

        Raises:
            PipelineError: If any processing step fails

        Example:
            ```python
            # Process with specific steps
            docs = pipeline.process_documents(
                steps={PipelineStep.LOAD, PipelineStep.SUMMARIZE},
                summary_config=SummarizerConfig(max_length=200),
                detect_pii=True
            )
            ```
        """
        try:
            # Default to all steps if none specified
            if steps is None:
                steps = set(PipelineStep)
            self.logger.info("Processing documents with steps: %s", steps)

            documents = []

            # Load documents
            if PipelineStep.LOAD in steps:
                self.logger.info("Loading documents from %s", self.config.export_dir)
                try:
                    documents = self.loader.process(documents)
                    if not documents:
                        self.logger.warning("No documents to process")
                        return []
                    self.logger.info("Loaded %d documents", len(documents))
                except Exception as e:
                    self.logger.error("Error loading documents: %s", str(e), exc_info=True)
                    raise

            # Process documents
            processing_steps = {
                PipelineStep.DEDUPLICATE,
                PipelineStep.PII,
                PipelineStep.SUMMARIZE,
                PipelineStep.EMBED,
                PipelineStep.CLUSTER,
            }
            if processing_steps & steps:  # If any processing steps are requested
                self.logger.info("Processing documents through pipeline steps")
                try:
                    documents = self.processor.process(
                        documents,
                        detect_pii=detect_pii and PipelineStep.PII in steps,
                        deduplicate=deduplicate and PipelineStep.DEDUPLICATE in steps,
                        summary_config=summary_config if PipelineStep.SUMMARIZE in steps else None,
                        cluster_config=cluster_config if PipelineStep.CLUSTER in steps else None,
                    )
                    self.logger.info("Processed %d documents", len(documents))
                except Exception as e:
                    self.logger.error("Error processing documents: %s", str(e), exc_info=True)
                    raise

            # Index documents
            if PipelineStep.INDEX in steps:
                self.logger.info("Indexing documents")
                try:
                    documents = self.indexer.process(
                        documents, deduplicate=False
                    )  # Already deduplicated
                    self.logger.info("Indexed %d documents", len(documents))
                except Exception as e:
                    self.logger.error("Error indexing documents: %s", str(e), exc_info=True)
                    raise

            return documents

        except Exception as e:
            error_msg = f"Pipeline execution failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise PipelineError(error_msg) from e

    def search(self, query: str = None, **kwargs) -> List[Dict]:
        """Search for documents using the specified query.

        Performs a semantic search across indexed documents using the provided query
        text and additional search parameters.

        Args:
            query (str, optional): The search query text. Defaults to None
            **kwargs: Additional search parameters passed to the search operations

        Returns:
            List[Dict]: List of matching documents with their search scores and metadata

        Example:
            ```python
            # Basic search
            results = pipeline.search("machine learning concepts")

            # Search with additional parameters
            results = pipeline.search(
                "machine learning",
                limit=10,
                min_score=0.5
            )
            ```
        """
        if query is not None:
            kwargs["query"] = query
        return self.search_ops.search(**kwargs)

    def update_document(self, doc_id: str, content: str = None, metadata: Dict = None) -> Dict:
        """Update an existing document in the index.

        Updates the content and/or metadata of a document identified by doc_id.
        At least one of content or metadata must be provided.

        Args:
            doc_id (str): The unique identifier of the document to update
            content (str, optional): New content for the document. Defaults to None
            metadata (Dict, optional): New metadata for the document. Defaults to None

        Returns:
            Dict: The updated document

        Raises:
            ValueError: If neither content nor metadata is provided
            PipelineError: If the update operation fails
        """
        return self.doc_ops.update_document(doc_id=doc_id, content=content, metadata=metadata)

    def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents from the index.

        Removes the specified documents from the vector index.

        Args:
            doc_ids (List[str]): List of document IDs to delete

        Returns:
            bool: True if all documents were successfully deleted, False otherwise

        Raises:
            PipelineError: If the deletion operation fails
        """
        return self.doc_ops.delete_documents(doc_ids)

    @property
    def doc_processor(self):
        """Get the document processor instance.

        Returns:
            DocumentProcessor: The configured document processor component
        """
        return self.processor

    @property
    def summarizer(self):
        """Get the document summarizer instance.

        Returns:
            DocumentSummarizer: The configured document summarizer component
        """
        return self.processor.summarizer

    @property
    def embedding_generator(self):
        """Get the embedding generator instance.

        Returns:
            EmbeddingGenerator: The configured embedding generator component
        """
        return self.processor.embedding_generator

    @property
    def topic_clusterer(self):
        """Get the topic clusterer instance.

        Returns:
            TopicClusterer: The configured topic clustering component
        """
        return self.processor.topic_clusterer

    @property
    def vector_index(self):
        """Get the vector index instance.

        Returns:
            VectorIndex: The configured vector index component
        """
        return self.indexer.vector_index

    def cleanup(self):
        """Clean up resources used by the pipeline.

        Performs cleanup operations such as closing connections and freeing resources.
        This method should be called when the pipeline is no longer needed.
        """
        self.logger.info("Cleaning up pipeline resources")
        try:
            components = [
                comp
                for comp in [self.loader, self.processor, self.indexer]
                if hasattr(self, comp.__class__.__name__.lower())
            ]
            for component in components:
                try:
                    component.cleanup()
                    self.logger.debug("Cleaned up %s", component.__class__.__name__)
                except Exception as e:
                    self.logger.error(
                        "Error cleaning up %s: %s",
                        component.__class__.__name__,
                        str(e),
                        exc_info=True,
                    )
            self.logger.info("Pipeline resources cleaned up successfully")
        except Exception as e:
            error_msg = f"Error during cleanup: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise PipelineError(error_msg) from e
