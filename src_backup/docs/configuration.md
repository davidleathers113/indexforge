# Configuration Guide

This guide details all configuration options available in the Direct Documentation Indexing module.

## Table of Contents

1. [Document Processing Configuration](#document-processing-configuration)
2. [Vector Generation Configuration](#vector-generation-configuration)
3. [Schema Configuration](#schema-configuration)
4. [Batch Processing Configuration](#batch-processing-configuration)
5. [Caching Configuration](#caching-configuration)

## Document Processing Configuration

### Excel Processor

```python
excel_config = {
    # Row processing
    "max_rows": 1000,              # Maximum rows to process per sheet
    "skip_sheets": ["Sheet2"],     # Sheets to skip during processing
    "required_columns": [          # Columns that must be present
        "Title",
        "Content"
    ],

    # Data cleaning
    "clean_headers": True,         # Clean and normalize column headers
    "remove_empty": True,          # Remove empty rows/columns
    "date_format": "%Y-%m-%d",     # Format for date columns

    # Error handling
    "skip_errors": False,          # Continue on row-level errors
    "error_log_path": "logs/",     # Path for error logging
}
```

### Word Processor

```python
word_config = {
    # Content extraction
    "extract_headers": True,       # Extract document headers
    "extract_tables": True,        # Extract tables from document
    "extract_images": False,       # Extract image metadata

    # Structure
    "preserve_formatting": False,  # Keep text formatting
    "include_comments": False,    # Include document comments
    "include_footnotes": True,    # Include footnotes

    # Parsing
    "max_depth": 3,              # Maximum header depth
    "table_format": "markdown"   # Format for extracted tables
}
```

## Vector Generation Configuration

### Embedding Generator

```python
embedding_config = {
    # Model settings
    "model": "text-embedding-3-small",  # OpenAI model to use
    "dimensions": 1536,                 # Vector dimensions

    # Chunking
    "chunk_size": 512,                  # Maximum chunk size
    "chunk_overlap": 50,                # Overlap between chunks

    # Caching
    "cache_ttl": 86400,                 # Cache TTL in seconds
    "cache_prefix": "emb",              # Cache key prefix

    # Performance
    "batch_size": 100,                  # Batch size for API calls
    "max_retries": 3,                   # Maximum retry attempts
    "retry_delay": 1                    # Delay between retries
}
```

## Schema Configuration

### Weaviate Schema

```python
schema_config = {
    "class": "Document",
    "description": "A document with vector embeddings",
    "vectorizer": "text2vec-transformers",

    # Vectorizer settings
    "moduleConfig": {
        "text2vec-transformers": {
            "vectorizeClassName": False,
            "model": "sentence-transformers-all-MiniLM-L6-v2",
            "poolingStrategy": "mean",
            "maxTokens": 512
        }
    },

    # Index configuration
    "vectorIndexConfig": {
        "distance": "cosine",
        "ef": 100,
        "efConstruction": 128,
        "maxConnections": 64,
        "vectorCacheMaxObjects": 500000
    }
}
```

## Batch Processing Configuration

### Batch Manager

```python
batch_config = {
    # Batch settings
    "batch_size": 200,           # Objects per batch
    "num_workers": 2,            # Parallel workers

    # Error handling
    "max_retries": 3,            # Maximum retry attempts
    "retry_delay": 1,            # Delay between retries
    "error_threshold": 0.1,      # Maximum error rate

    # Progress tracking
    "show_progress": True,       # Show progress bar
    "log_interval": 10,          # Log interval in seconds

    # Resource management
    "cleanup_interval": 300,     # Cleanup interval
    "max_memory": "2G"          # Maximum memory usage
}
```

## Caching Configuration

### Cache Manager

```python
cache_config = {
    # Redis settings
    "host": "localhost",
    "port": 6379,
    "db": 0,

    # Cache settings
    "prefix": "cache",
    "default_ttl": 3600,
    "max_size": "1G",

    # Connection
    "socket_timeout": 5,
    "socket_connect_timeout": 2,
    "retry_on_timeout": True,

    # Error handling
    "max_retries": 3,
    "retry_delay": 1
}
```

## Environment Variables

The following environment variables can be used to override configuration:

```bash
# Vector Generation
OPENAI_API_KEY=your-api-key
EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=512

# Weaviate
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-api-key

# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-password

# Processing
BATCH_SIZE=200
NUM_WORKERS=2
MAX_RETRIES=3
```

## Configuration Precedence

Configuration values are loaded in the following order (later overrides earlier):

1. Default values in code
2. Configuration files
3. Environment variables
4. Runtime configuration

## Best Practices

1. **Memory Management**

   - Set appropriate batch sizes
   - Enable cleanup intervals
   - Monitor memory usage

2. **Error Handling**

   - Configure retry mechanisms
   - Set error thresholds
   - Enable logging

3. **Performance**

   - Optimize chunk sizes
   - Configure caching
   - Use parallel processing

4. **Security**
   - Use environment variables for secrets
   - Configure timeouts
   - Set appropriate permissions
