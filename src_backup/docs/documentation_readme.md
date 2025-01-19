# Direct Documentation Indexing

This module provides functionality for indexing and processing exported document files (Excel, Word, etc.) into a Weaviate vector database. It handles document parsing, text extraction, vector embedding generation, and efficient batch indexing.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Architecture](#architecture)
5. [Components](#components)
6. [Configuration](#configuration)
7. [Examples](#examples)
8. [API Reference](#api-reference)
9. [Performance Considerations](#performance-considerations)
10. [Troubleshooting](#troubleshooting)

## Overview

The Direct Documentation Indexing module is designed to:

- Process exported document files (Excel, Word, etc.)
- Extract and clean text content
- Generate vector embeddings
- Efficiently batch index into Weaviate
- Provide search and retrieval capabilities

### Key Features

- **Document Processing**

  - Excel file processing (.xlsx, .csv)
  - Word document processing (.docx)
  - Configurable text chunking
  - Content cleaning and normalization

- **Vector Operations**

  - OpenAI embeddings integration
  - Vector normalization
  - Caching with retry mechanisms
  - "Bring Your Own Vectors" support

- **Batch Processing**

  - Configurable batch sizes
  - Error handling and retries
  - Resource cleanup
  - Progress tracking

- **Schema Management**
  - Automatic schema creation
  - Schema validation
  - Version management
  - Migration support

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from src.connectors.direct_documentation_indexing import DocumentConnector

# Initialize connector
connector = DocumentConnector()

# Process a document
result = connector.process_file("path/to/document.xlsx")

# Check processing status
if result["status"] == "success":
    print("Document processed successfully")
    print(f"Extracted content: {result['content']}")
else:
    print(f"Processing failed: {result['error']}")
```

## Architecture

The module follows a modular architecture with clear separation of concerns:

1. **Connector Layer** (`connector.py`)

   - Main entry point
   - File type detection
   - Processor routing

2. **Processor Layer** (`processors/`)

   - File-specific processing
   - Content extraction
   - Data normalization

3. **Vector Layer** (`src/embeddings/`)

   - Embedding generation
   - Vector normalization
   - Caching

4. **Index Layer** (`src/indexing/`)
   - Schema management
   - Batch operations
   - Search functionality

## Components

### Document Connector

The main entry point for document processing:

```python
class DocumentConnector:
    """Connector for processing exported document files."""

    def process_file(self, file_path: str) -> Dict:
        """Process a document file."""
        ...
```

### Processors

#### Excel Processor

Handles Excel and CSV files:

```python
class ExcelProcessor(BaseProcessor):
    """Processor for Excel files (.xlsx, .csv)."""

    SUPPORTED_EXTENSIONS = {".xlsx", ".csv", ".xls"}
```

Features:

- Sheet data extraction
- Column validation
- Basic statistics
- NaN handling

#### Word Processor

Handles Word documents:

```python
class WordProcessor(BaseProcessor):
    """Processor for Word documents (.docx)."""

    SUPPORTED_EXTENSIONS = {".docx"}
```

Features:

- Text extraction
- Header parsing
- Table extraction
- Image metadata

## Configuration

Configuration options can be provided when initializing processors:

```python
config = {
    "excel": {
        "max_rows": 1000,
        "skip_sheets": ["Sheet2"],
        "required_columns": ["Title", "Content"]
    },
    "word": {
        "extract_headers": True,
        "extract_tables": True,
        "extract_images": False
    }
}
```

## Examples

### Processing an Excel File

```python
from src.connectors.direct_documentation_indexing import DocumentConnector

connector = DocumentConnector()
result = connector.process_file("data.xlsx")

# Access sheet data
for sheet_name, data in result["content"]["sheets"].items():
    print(f"Sheet: {sheet_name}")
    print(f"Rows: {data['stats']['row_count']}")
    print(f"Columns: {data['stats']['columns']}")
```

### Processing a Word Document

```python
result = connector.process_file("document.docx")

# Access document content
content = result["content"]
print(f"Full text: {content['full_text']}")
print(f"Headers: {content['headers']}")
print(f"Tables: {content['tables']}")
```

## Performance Considerations

1. **Batch Processing**

   - Default batch size: 200 objects
   - Configurable parallelization
   - Automatic retries

2. **Caching**

   - Redis-based caching
   - Configurable TTL
   - Retry mechanisms

3. **Memory Management**
   - Lazy loading for large files
   - Chunk-based processing
   - Resource cleanup

## Troubleshooting

Common issues and solutions:

1. **File Processing Errors**

   ```python
   {"status": "error", "message": "No suitable processor found"}
   ```

   - Check file extension
   - Verify file permissions
   - Ensure file is not corrupted

2. **Memory Issues**

   - Configure batch size
   - Enable lazy loading
   - Use chunking

3. **Cache Issues**
   - Verify Redis connection
   - Check cache configuration
   - Monitor cache size
