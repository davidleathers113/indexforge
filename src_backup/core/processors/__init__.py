"""Document processor package for content extraction.

This package provides processors for extracting content from various document
types, including Excel files and Word documents. Each processor implements a
common interface defined by the BaseProcessor class.

Example:
    ```python
    from pathlib import Path
    from src.core.processors import ExcelProcessor, WordProcessor

    excel_processor = ExcelProcessor({
        "max_rows": 1000,
        "required_columns": ["ID", "Name"]
    })

    word_processor = WordProcessor({
        "extract_headers": True,
        "extract_tables": True
    })

    file_path = Path("document.xlsx")
    if excel_processor.can_process(file_path):
        result = excel_processor.process(file_path)
        if result.status == "success":
            print(f"Processed {result.content['metadata']['file_name']}")
    ```
"""

from .base import BaseProcessor, ProcessingResult
from .excel import ExcelProcessor, SheetData
from .word import HeaderData, TableData, WordProcessor


__all__ = [
    "BaseProcessor",
    "ExcelProcessor",
    "HeaderData",
    "ProcessingResult",
    "SheetData",
    "TableData",
    "WordProcessor",
]
