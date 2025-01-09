"""Direct documentation indexing module for document file processing.

This module provides functionality for processing and indexing various types of
document files directly from the filesystem. It includes:
- Document connector for managing file processing
- Specialized processors for different file types (Excel, Word)
- Common processing utilities and base classes

The module supports automatic file type detection, content extraction,
and conversion into a standardized document format suitable for indexing.

Example:
    ```python
    from src.connectors.direct_documentation_indexing import (
        DocumentConnector,
        ExcelProcessor,
        WordProcessor
    )

    # Configure processors
    processors = [
        ExcelProcessor(sheet_names=["Data", "Summary"]),
        WordProcessor(extract_headers=True)
    ]

    # Initialize connector
    connector = DocumentConnector(
        source_dir="/path/to/docs",
        processors=processors
    )

    # Process documents
    documents = connector.load_documents()
    ```

Components:
    - DocumentConnector: Main interface for document processing
    - ExcelProcessor: Handles Excel workbooks and spreadsheets
    - WordProcessor: Processes Word documents and rich text

Note:
    Each processor implements a common interface defined by BaseProcessor,
    ensuring consistent document processing across different file types.
    The processed documents follow a standardized format with content,
    metadata, and optional vector embeddings.
"""

from .connector import DocumentConnector
from .processors.excel_processor import ExcelProcessor
from .processors.word_processor import WordProcessor

__all__ = ["DocumentConnector", "ExcelProcessor", "WordProcessor"]
