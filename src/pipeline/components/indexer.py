"""Document indexer component for managing vector search indices.

This module provides functionality for indexing documents in a vector search
engine, enabling efficient semantic search and retrieval. It handles:
- Document validation before indexing
- Vector index management
- Batch indexing operations
- Deduplication during indexing

Main Components:
    - DocumentIndexer: Core class for managing document indices
"""


from src.indexing.vector_index import VectorIndex
from src.pipeline.components.base import PipelineComponent
from src.pipeline.errors import IndexingError


class DocumentIndexer(PipelineComponent):
    """Component for managing document indexing in vector search engine.

    This class handles the indexing of documents in a vector search engine,
    ensuring proper validation, batching, and error handling during the
    indexing process.

    Attributes:
        config (PipelineConfig): Configuration settings including index URL
        logger (logging.Logger): Component logger
        vector_index (VectorIndex): Vector search index client

    Examples:
        >>> indexer = DocumentIndexer(config)
        >>> docs = [{"content": {"body": "text"}, "embeddings": {"body": [0.1, 0.2]}}]
        >>> indexed = indexer.process(docs)
    """

    def __init__(self, *args, **kwargs):
        """Initialize document indexer.

        Args:
            *args: Variable length argument list passed to parent class
            **kwargs: Arbitrary keyword arguments passed to parent class

        Raises:
            IndexingError: If vector index initialization fails
        """
        super().__init__(*args, **kwargs)

        try:
            self.vector_index = VectorIndex(
                client_url=self.config.index_url,
                class_name=self.config.class_name,
                batch_size=self.config.batch_size,
            )
        except Exception as e:
            self.logger.error("Failed to initialize vector index: %s", str(e))
            raise IndexingError("Vector index initialization failed") from e

    def process(self, documents: list[dict], deduplicate: bool = True, **kwargs) -> list[dict]:
        """Process documents by indexing them in the vector search engine.

        Args:
            documents: List of documents to index, must contain embeddings
            deduplicate: Whether to check for and skip duplicate documents
            **kwargs: Additional keyword arguments for customizing indexing

        Returns:
            List[Dict]: List of successfully indexed documents

        Raises:
            IndexingError: If indexing fails
        """
        if not documents:
            return []

        try:
            # Index documents in batches
            indexed_docs = []
            for i in range(0, len(documents), self.config.batch_size):
                batch = documents[i : i + self.config.batch_size]
                try:
                    self.vector_index.index_documents(batch, deduplicate=deduplicate)
                    indexed_docs.extend(batch)
                except Exception as e:
                    self.logger.error("Failed to index batch: %s", str(e))
                    continue

            return indexed_docs

        except Exception as e:
            self.logger.error("Failed to process documents for indexing: %s", str(e))
            raise IndexingError("Document indexing failed") from e

    def cleanup(self):
        """Clean up indexer resources.

        This method ensures proper cleanup of the vector index client connection.

        Raises:
            IndexingError: If cleanup fails
        """
        try:
            if hasattr(self, "vector_index"):
                self.vector_index.close()
        except Exception as e:
            self.logger.error("Failed to clean up vector index: %s", str(e))
            raise IndexingError("Vector index cleanup failed") from e
