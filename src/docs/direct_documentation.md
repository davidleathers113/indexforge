# Direct Documentation Indexing with Weaviate

A robust document indexing system built on Weaviate, featuring semantic search, cross-referencing, and comprehensive source tracking.

## Configuration

### Environment Variables

```env
# Required Configuration
WEAVIATE_URL=http://localhost:8080                # Weaviate instance URL
OPENAI_API_KEY=your-api-key                       # OpenAI API key for embeddings
BATCH_SIZE=100                                    # Number of objects per batch

# Optional Configuration
VECTOR_CACHE_DIR=./cache                          # Directory for vector caching
MAX_RETRIES=3                                     # Maximum retry attempts for failed operations
CHUNK_SIZE=1000                                   # Default chunk size in characters
CHUNK_OVERLAP=100                                 # Overlap between chunks
```

### Schema Definition

The system uses a predefined schema for document indexing. Here's an example schema:

```python
schema = {
    "class": "Document",
    "vectorizer": "text2vec-openai",
    "moduleConfig": {
        "text2vec-openai": {
            "model": "ada-002",
            "modelVersion": "002",
            "type": "text"
        }
    },
    "properties": [
        {
            "name": "content",
            "dataType": ["text"],
            "moduleConfig": {
                "text2vec-openai": {
                    "skip": False,
                    "vectorizePropertyName": False
                }
            }
        },
        {
            "name": "source",
            "dataType": ["string"]
        },
        {
            "name": "references",
            "dataType": ["Document"]
        }
    ]
}
```

## Batch Processing

Example implementation for batch document processing:

```python
from typing import List
import weaviate
from tenacity import retry, stop_after_attempt, wait_exponential

class DocumentBatchProcessor:
    def __init__(self, client: weaviate.Client, batch_size: int = 100):
        self.client = client
        self.batch_size = batch_size

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def process_batch(self, documents: List[dict]) -> None:
        with self.client.batch as batch:
            batch.batch_size = self.batch_size
            for doc in documents:
                batch.add_data_object(
                    data_object=doc,
                    class_name="Document"
                )
```

## Error Handling

Common errors and their resolutions:

### Schema Mismatch

```python
try:
    client.schema.create_class(schema)
except weaviate.exceptions.UnexpectedStatusCodeException as e:
    if "already exists" in str(e):
        # Handle existing schema
        client.schema.update_class(schema)
    else:
        raise
```

### Rate Limits

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def vectorize_with_backoff(text: str) -> List[float]:
    # Implementation with automatic retries
    pass
```

## Performance Optimization

1. **Batch Processing**

   - Use batch sizes between 100-500 objects
   - Enable batch configuration with `client.batch.configure()`

2. **Vector Caching**

   - Implement vector caching for frequently accessed documents
   - Use the `VECTOR_CACHE_DIR` configuration

3. **Schema Optimization**

   - Index only necessary properties
   - Use appropriate data types for properties
   - Configure vectorization settings per property

4. **Query Optimization**
   - Use cursor-based pagination for large result sets
   - Implement proper filtering at the query level
   - Utilize vector caching for frequent searches

## API Reference

### Document Operations

```python
class DocumentIndexer:
    def index_document(self, content: str, metadata: dict) -> str:
        """
        Index a single document with metadata.

        Args:
            content (str): Document content
            metadata (dict): Document metadata

        Returns:
            str: Document ID
        """
        pass

    def batch_index(self, documents: List[dict]) -> List[str]:
        """
        Batch index multiple documents.

        Args:
            documents (List[dict]): List of document dictionaries

        Returns:
            List[str]: List of document IDs
        """
        pass

    def search(self, query: str, limit: int = 10) -> List[dict]:
        """
        Perform semantic search.

        Args:
            query (str): Search query
            limit (int): Maximum number of results

        Returns:
            List[dict]: Search results
        """
        pass
```

## Example Configurations

### Basic Configuration

```yaml
indexing:
  batch_size: 100
  chunk_size: 1000
  chunk_overlap: 100
  vector_cache: true

weaviate:
  url: http://localhost:8080
  timeout: 300

vectorizer:
  provider: openai
  model: text-embedding-ada-002

monitoring:
  enabled: true
  log_level: INFO
```

### Production Configuration

```yaml
indexing:
  batch_size: 500
  chunk_size: 1500
  chunk_overlap: 150
  vector_cache: true
  cache_dir: /path/to/cache

weaviate:
  url: https://production-weaviate:8080
  timeout: 600
  retries: 3

vectorizer:
  provider: openai
  model: text-embedding-ada-002
  batch_size: 50

monitoring:
  enabled: true
  log_level: WARNING
  alerts:
    email: alerts@company.com
    slack_webhook: https://hooks.slack.com/services/xxx
```
