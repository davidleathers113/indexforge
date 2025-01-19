"""Document operations implementation.

This module provides document-level operations for the pipeline, including
document updates, deletions, and metadata management. It integrates with
the vector index and embedding generator for document processing.

Features:
1. Document Management:
   - Document updates
   - Document deletions
   - Metadata management
   - Content processing

2. Content Processing:
   - Text summarization
   - Embedding generation
   - Content validation
   - Format standardization

3. Index Integration:
   - Vector index updates
   - Document storage
   - Relationship management
   - Query optimization

Usage:
    ```python
    from pipeline.document_ops import DocumentOperations
    from src.embeddings.embedding_generator import EmbeddingGenerator
    from src.indexing.vector_index import VectorIndex
    from src.utils.summarizer.core.processor import DocumentSummarizer

    # Initialize document operations
    doc_ops = DocumentOperations(
        summarizer=summarizer,
        embedding_generator=embedding_generator,
        vector_index=vector_index,
        logger=logger
    )

    # Update document
    success = doc_ops.update_document(
        doc_id="doc123",
        content="Updated content",
        metadata={"author": "John Doe"}
    )
    ```

Note:
    - Handles document lifecycle
    - Maintains data consistency
    - Provides error handling
    - Includes detailed logging
"""

import logging

from src.embeddings.embedding_generator import EmbeddingGenerator
from src.indexing.vector_index import VectorIndex
from src.utils.summarizer.config.settings import SummarizerConfig
from src.utils.summarizer.core.processor import DocumentSummarizer


logger = logging.getLogger(__name__)


class DocumentOperations:
    """Document operations class.

    This class provides a unified interface for document-level operations,
    including updates, deletions, and metadata management. It integrates
    with various components for document processing.
    """

    def __init__(
        self,
        summarizer: DocumentSummarizer,
        embedding_generator: EmbeddingGenerator,
        vector_index: VectorIndex,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize document operations.

        Args:
            summarizer: For document summarization
            embedding_generator: For generating document embeddings
            vector_index: For document storage and retrieval
            logger: Optional logger instance
        """
        self.summarizer = summarizer
        self.embedding_generator = embedding_generator
        self.vector_index = vector_index
        self.logger = logger or logging.getLogger(__name__)

    def update_document(
        self,
        doc_id: str,
        content: str = None,
        metadata: dict = None,
        summary_config: SummarizerConfig | None = None,
    ) -> bool:
        """Update a document in the vector index.

        Updates document content and/or metadata, optionally generating
        new summaries and embeddings as needed.

        Args:
            doc_id: ID of the document to update
            content: New content for the document
            metadata: New metadata for the document
            summary_config: Optional summary configuration

        Returns:
            True if successful, False otherwise

        Example:
            >>> success = doc_ops.update_document(
            ...     doc_id="doc123",
            ...     content="New content",
            ...     metadata={"status": "updated"}
            ... )
        """
        try:
            self.logger.debug("Starting document update process for document: %s", doc_id)

            # Create document structure
            document = {
                "id": doc_id,
                "content": {"body": content} if content else {},
                "metadata": metadata or {},
            }

            # Generate summary if needed
            if summary_config and content:
                self.logger.debug("Generating summary with config: %s", vars(summary_config))
                processed_docs = self.summarizer.process_documents([document], summary_config)
                if not processed_docs:
                    self.logger.error("Failed to process document for update")
                    return False
                document = processed_docs[0]
                self.logger.debug("Successfully generated summary")

            # Generate embeddings if content provided
            if content:
                self.logger.debug("Generating embeddings for document")
                documents = self.embedding_generator.generate_embeddings([document])
                if not documents:
                    self.logger.error("Failed to generate embeddings for update")
                    return False
                document = documents[0]
                self.logger.debug("Successfully generated embeddings")

            # Update in vector index
            self.logger.debug("Updating document in vector index")
            success = self.vector_index.update_documents([document])
            if not success:
                self.logger.error("Failed to update document in vector index")
                return False
            self.logger.debug("Successfully updated document in vector index")

            return True

        except Exception as e:
            self.logger.error(f"Error updating document: {e!s}")
            return False

    def delete_documents(self, doc_ids: list[str]) -> bool:
        """Delete documents from the vector index.

        Removes specified documents from the vector index, handling cleanup
        and relationship management.

        Args:
            doc_ids: List of document IDs to delete

        Returns:
            True if successful, False otherwise

        Example:
            >>> success = doc_ops.delete_documents(["doc123", "doc456"])
        """
        try:
            self.logger.debug("Attempting to delete %d documents: %s", len(doc_ids), doc_ids)
            success = self.vector_index.delete_documents(doc_ids)
            if not success:
                self.logger.error("Failed to delete documents from vector index")
                return False
            self.logger.debug("Successfully deleted documents from vector index")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting documents: {e!s}")
            return False
