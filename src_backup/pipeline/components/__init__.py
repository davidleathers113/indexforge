"""Pipeline components package for document processing workflow.

This package provides the core components that make up the document processing
pipeline. Each component is responsible for a specific aspect of document
processing, such as loading, processing, or indexing documents. Components can
be composed to create custom processing workflows.

Classes:
    PipelineComponent: Base class for all pipeline components
    DocumentIndexer: Component for indexing processed documents
    DocumentLoader: Component for loading documents from various sources
    DocumentProcessor: Component for document processing operations

Example:
    ```python
    from src.pipeline.components import (
        DocumentLoader,
        DocumentProcessor,
        DocumentIndexer
    )

    # Initialize components
    loader = DocumentLoader(
        source_dir="path/to/documents",
        batch_size=100
    )

    processor = DocumentProcessor(
        enable_summarization=True,
        enable_embedding=True
    )

    indexer = DocumentIndexer(
        index_url="http://localhost:8080",
        class_name="Document"
    )

    # Process documents through components
    documents = loader.process([])  # Load documents
    documents = processor.process(documents)  # Process documents
    documents = indexer.process(documents)  # Index documents
    ```

Note:
    Components are designed to be modular and reusable. Each component implements
    a common interface defined by the PipelineComponent base class, making it easy
    to extend and customize the pipeline with new functionality.
"""

from .base import PipelineComponent
from .indexer import DocumentIndexer
from .loader import DocumentLoader
from .processor import DocumentProcessor


__all__ = [
    "DocumentIndexer",
    "DocumentLoader",
    "DocumentProcessor",
    "PipelineComponent",
]
