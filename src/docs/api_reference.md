# API Reference

## DocumentConnector

Main class for processing and indexing documents.

### Methods

#### `__init__(self, config: Optional[Dict[str, Any]] = None)`

Initialize the document connector.

**Parameters:**

- `config` (Optional[Dict[str, Any]]): Configuration dictionary with processor-specific settings

**Example:**

```python
connector = DocumentConnector({
    "excel": {
        "max_rows": 1000,
        "skip_sheets": ["Sheet2"]
    },
    "word": {
        "extract_headers": True
    }
})
```

#### `process_file(self, file_path: Union[str, Path]) -> Dict[str, Any]`

Process a document file.

**Parameters:**

- `file_path` (Union[str, Path]): Path to the file to process

**Returns:**

- Dict[str, Any]: Processing result containing:
  - `status`: "success" or "error"
  - `content`: Extracted content (if successful)
  - `error`: Error message (if failed)

**Example:**

```python
result = connector.process_file("document.xlsx")
if result["status"] == "success":
    content = result["content"]
```

## Processors

### ExcelProcessor

Processor for Excel files (.xlsx, .csv, .xls).

#### `__init__(self, config: Optional[Dict[str, Any]] = None)`

Initialize the Excel processor.

**Parameters:**

- `config` (Optional[Dict[str, Any]]): Configuration with settings:
  - `max_rows`: Maximum number of rows to process
  - `skip_sheets`: Sheets to skip
  - `required_columns`: Columns that must be present

**Example:**

```python
processor = ExcelProcessor({
    "max_rows": 1000,
    "skip_sheets": ["Sheet2"],
    "required_columns": ["Title", "Content"]
})
```

#### `process(self, file_path: Path) -> Dict[str, Any]`

Process an Excel file.

**Parameters:**

- `file_path` (Path): Path to the Excel file

**Returns:**

- Dict[str, Any]: Processing result containing:
  - `status`: Processing status
  - `content`: Dict with sheet data and metadata
  - `error`: Error message if failed

### WordProcessor

Processor for Word documents (.docx).

#### `__init__(self, config: Optional[Dict[str, Any]] = None)`

Initialize the Word processor.

**Parameters:**

- `config` (Optional[Dict[str, Any]]): Configuration with settings:
  - `extract_headers`: Whether to extract headers
  - `extract_tables`: Whether to extract tables
  - `extract_images`: Whether to extract image metadata

**Example:**

```python
processor = WordProcessor({
    "extract_headers": True,
    "extract_tables": True,
    "extract_images": False
})
```

#### `process(self, file_path: Path) -> Dict[str, Any]`

Process a Word document.

**Parameters:**

- `file_path` (Path): Path to the Word document

**Returns:**

- Dict[str, Any]: Processing result containing:
  - `status`: Processing status
  - `content`: Dict with document content and metadata
  - `error`: Error message if failed

## Schema Management

### SchemaDefinition

Defines schema structure and properties.

#### `get_schema(cls, class_name: str) -> Dict`

Get schema definition.

**Parameters:**

- `class_name` (str): Name of the document class

**Returns:**

- Dict: Schema definition dictionary

**Example:**

```python
schema = SchemaDefinition.get_schema("Document")
```

### SchemaValidator

Validates schema configuration and version.

#### `__init__(self, client: weaviate.Client, class_name: str)`

Initialize schema validator.

**Parameters:**

- `client` (weaviate.Client): Weaviate client instance
- `class_name` (str): Name of the document class

#### `validate_schema(self, schema: Dict) -> bool`

Validate schema configuration.

**Parameters:**

- `schema` (Dict): Schema configuration to validate

**Returns:**

- bool: True if schema is valid

## Batch Processing

### BatchManager

Manages document batch operations.

#### `__init__(self, client: weaviate.Client, class_name: str, batch_size: int)`

Initialize batch manager.

**Parameters:**

- `client` (weaviate.Client): Weaviate client instance
- `class_name` (str): Name of the document class
- `batch_size` (int): Size of document batches

#### `add_document(self, properties: Dict, vector: List[float], doc_id: str) -> None`

Add document to current batch.

**Parameters:**

- `properties` (Dict): Document properties
- `vector` (List[float]): Document vector
- `doc_id` (str): Document ID

## Vector Operations

### EmbeddingGenerator

Generates embeddings for documents.

#### `__init__(self, model: str = "text-embedding-3-small", chunk_size: int = 512)`

Initialize the embedding generator.

**Parameters:**

- `model` (str): The OpenAI model to use
- `chunk_size` (int): Maximum size of text chunks

#### `generate_embeddings(self, documents: List[Dict]) -> List[Dict]`

Generate embeddings for documents.

**Parameters:**

- `documents` (List[Dict]): List of document dictionaries

**Returns:**

- List[Dict]: Documents with added embeddings

## Caching

### CacheManager

Manages caching operations.

#### `__init__(self, host: str = "localhost", port: int = 6379, prefix: str = "cache")`

Initialize cache manager.

**Parameters:**

- `host` (str): Redis host
- `port` (int): Redis port
- `prefix` (str): Cache key prefix

#### `cache_decorator(self, key_prefix: str, ttl: Optional[int] = None)`

Decorator to cache function results.

**Parameters:**

- `key_prefix` (str): Prefix for cache key
- `ttl` (Optional[int]): Optional TTL in seconds

**Example:**

```python
@cache_manager.cache_decorator("docs")
def process_document(doc_id: str) -> Dict:
    # Process document
    return result
```
