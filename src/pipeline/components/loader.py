"""Document loader component for importing and standardizing documents.

This module provides functionality for loading documents from various sources
(e.g., Google Workspace, Notion) and transforming them into a standardized
format suitable for processing by the pipeline.

The loader handles:
- Document source detection and connection
- Content extraction and cleaning
- Metadata standardization
- Document ID generation and tracking

Main Components:
    - DocumentLoader: Core class for loading and standardizing documents
"""

import uuid
from typing import Dict, List, Optional

from src.connectors.notion_connector import NotionConnector
from src.pipeline.components.base import PipelineComponent
from src.pipeline.errors import LoaderError


class DocumentLoader(PipelineComponent):
    """Component for loading and standardizing documents from various sources.

    This class handles the loading of documents from different sources and
    transforms them into a standardized format with consistent structure,
    metadata, and identifiers.

    Attributes:
        config (PipelineConfig): Configuration settings including source paths
        logger (logging.Logger): Component logger
        processed_files (Set[str]): Set of processed file paths
        failed_files (Dict[str, str]): Map of file paths to error messages

    Examples:
        >>> loader = DocumentLoader(config)
        >>> documents = loader.process()
        >>> print(f"Loaded {len(documents)} documents")
    """

    def __init__(self, notion_connector: Optional[NotionConnector] = None, *args, **kwargs):
        """Initialize document loader.

        Args:
            notion_connector: Optional NotionConnector instance to use
            *args: Variable length argument list passed to parent class
            **kwargs: Arbitrary keyword arguments passed to parent class

        Raises:
            LoaderError: If initialization fails
        """
        super().__init__(*args, **kwargs)
        self.processed_files = set()
        self.failed_files = {}

        try:
            self.notion = notion_connector or NotionConnector(self.config.export_dir)
            self.logger.debug("Notion connector initialized")
        except Exception as e:
            self.logger.error("Failed to initialize Notion connector: %s", str(e))
            raise LoaderError("Notion connector initialization failed") from e

    def process(self, documents: Optional[List[Dict]] = None, **kwargs) -> List[Dict]:
        """Process and standardize documents from the source.

        If documents are provided, processes those. Otherwise, loads documents
        from the configured source directory.

        Args:
            documents: Optional list of pre-loaded documents to process
            **kwargs: Additional keyword arguments for customizing processing

        Returns:
            List[Dict]: List of standardized documents with consistent structure

        Raises:
            LoaderError: If document loading or processing fails
        """
        if documents:
            return self._process_documents(documents)

        try:
            self.logger.debug("Starting document loading process")
            raw_docs = self._load_documents()
            self.logger.debug("Successfully loaded %d raw documents", len(raw_docs))
            processed_docs = self._process_documents(raw_docs)
            self.logger.debug("Successfully processed %d documents", len(processed_docs))
            return processed_docs
        except Exception as e:
            self.logger.error("Failed to load documents: %s", str(e))
            raise LoaderError("Document loading failed") from e

    def _process_documents(self, documents: List[Dict]) -> List[Dict]:
        """Process a list of raw documents into standardized format.

        Args:
            documents: List of raw documents from the source

        Returns:
            List[Dict]: List of processed documents with standardized structure

        Raises:
            LoaderError: If document processing fails
        """
        self.logger.debug("Starting document processing for %d documents", len(documents))
        processed_docs = []
        for i, doc in enumerate(documents, 1):
            self.logger.debug("Processing document %d/%d", i, len(documents))
            try:
                # Extract content and metadata
                body = self._extract_body(doc)
                metadata = self._extract_metadata(doc)

                # Create standardized document
                processed_doc = {
                    "id": str(uuid.uuid4()),
                    "content": {"body": body, "summary": None},
                    "metadata": metadata,
                    "embeddings": {
                        "version": None,
                        "model": None,
                        "body": None,
                        "summary": None,
                    },
                }
                self.logger.debug("Generated document ID: %s", processed_doc["id"])
                processed_docs.append(processed_doc)

            except Exception as e:
                self.logger.error("Failed to process document %d/%d: %s", i, len(documents), str(e))
                self.logger.debug("Failed document content: %s", str(doc))
                continue

        return processed_docs

    def _extract_body(self, doc: Dict) -> str:
        """Extract the main text content from a document.

        Args:
            doc: Raw document dictionary containing content

        Returns:
            str: Extracted and cleaned main text content

        Examples:
            >>> doc = {"source": "google_workspace", "content": {"full_text": "Hello"}}
            >>> loader._extract_body(doc)
            'Hello'
        """
        # Handle Google Workspace documents
        if doc.get("source") == "google_workspace":
            return doc.get("content", {}).get("full_text", "").strip()

        # Handle Notion documents
        if doc.get("source") == "notion":
            return doc.get("content", {}).get("body", "").strip()

        # Default to raw content
        return str(doc.get("content", "")).strip()

    def _load_documents(self) -> List[Dict]:
        """Load documents from the configured source directory.

        Returns:
            List[Dict]: List of raw documents from the source

        Raises:
            LoaderError: If document loading fails
        """
        try:
            self.logger.debug(
                "Attempting to load CSV files from Notion export at: %s", self.config.export_dir
            )
            dataframes = self.notion.load_csv_files()
            self.logger.debug("Successfully loaded CSV files")

            documents = self.notion.normalize_data(dataframes)
            self.logger.info("Loaded %d documents from Notion export", len(documents))
            if documents:
                self.logger.debug("First document sample: %s", str(documents[0]))

            return documents
        except Exception as e:
            self.logger.error("Failed to load documents: %s", str(e))
            raise LoaderError(f"Document loading failed: {str(e)}") from e

    def _extract_metadata(self, doc: Dict) -> Dict:
        """Extract and standardize metadata from a document.

        Args:
            doc: Raw document dictionary containing metadata

        Returns:
            Dict: Standardized metadata dictionary with source-specific fields

        Examples:
            >>> doc = {"source": "google_workspace", "metadata": {"title": "Test"}}
            >>> metadata = loader._extract_metadata(doc)
            >>> metadata["title"]
            'Test'
        """
        metadata = doc.get("metadata", {}).copy()
        metadata["processor"] = self.__class__.__name__
        metadata["source"] = doc.get("source", "unknown")
        return metadata
