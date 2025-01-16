"""Document processor package for file type-specific processing.

This package provides specialized processors for handling different types of
document files. Each processor implements a common interface defined by
BaseProcessor, ensuring consistent document processing across file types.

The package includes:
- Base processor interface and common utilities
- Excel workbook and spreadsheet processor
- Word document and rich text processor

Example:
    ```python
    from src.connectors.direct_documentation_indexing.processors import (
        BaseProcessor,
        ExcelProcessor,
        WordProcessor
    )

    # Configure processors
    excel_proc = ExcelProcessor(
        sheet_names=["Data", "Summary"],
        header_row=0
    )
    word_proc = WordProcessor(
        extract_headers=True,
        include_metadata=True
    )

    # Process files
    if excel_proc.can_process(file_path):
        doc = excel_proc.process(file_path)
    elif word_proc.can_process(file_path):
        doc = word_proc.process(file_path)
    ```

Components:
    - BaseProcessor: Abstract base class defining processor interface
    - ExcelProcessor: Handles Excel (.xlsx, .xls) files
    - WordProcessor: Processes Word (.docx, .doc) files

Note:
    All processors convert their specific file types into a standardized
    document format containing:
    - Extracted text content
    - Document metadata
    - File information
    - Processing status
"""

from .base_processor import BaseProcessor
from .excel_processor import ExcelProcessor
from .word_processor import WordProcessor


__all__ = ["BaseProcessor", "ExcelProcessor", "WordProcessor"]
