"""Data source connectors package for document import and processing.

This package provides connectors for importing and processing documents from
various data sources, including:
- Notion workspace exports (CSV, HTML, Markdown)
- Direct documentation files (Excel, Word, PDF)

Each connector handles source-specific data extraction, validation, and
conversion into a standardized document format suitable for indexing.

Example:
    ```python
    from src.connectors import NotionConnector, DocumentConnector

    # Import from Notion export
    notion = NotionConnector("/path/to/notion/export")
    notion_docs = notion.load_documents()

    # Import from documentation files
    docs = DocumentConnector(
        source_dir="/path/to/docs",
        file_types=["xlsx", "docx", "pdf"]
    )
    doc_files = docs.load_documents()
    ```

Components:
    - NotionConnector: Handles Notion workspace exports
    - DocumentConnector: Processes direct documentation files

Note:
    All connectors convert source documents into a standardized format with:
    - Content (body text, summaries)
    - Metadata (title, timestamps, source info)
    - Relationships (parent/child, references)
    - Embeddings (vector representations)
"""

from .documentation import DocumentConnector
from .notion_connector import NotionConnector


__all__ = ["DocumentConnector", "NotionConnector"]
