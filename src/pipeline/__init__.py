"""Pipeline package for processing Notion exports.

This package provides a comprehensive pipeline system for processing and indexing
document exports. It includes components for document loading, processing,
and indexing, with support for various document formats and processing steps.

Components:
1. Core Pipeline:
   - Pipeline orchestration and management
   - Resource handling and cleanup
   - Error handling and recovery
   - Progress tracking

2. Processing Steps:
   - Document loading and validation
   - Content extraction and normalization
   - Metadata processing
   - PII detection
   - Text summarization
   - Embedding generation
   - Topic clustering
   - Vector indexing

3. Operations:
   - Document operations (update, delete)
   - Search operations (semantic, hybrid)
   - Batch processing
   - Cache management

4. Configuration:
   - Parameter validation
   - Environment integration
   - Resource configuration
   - Performance tuning

Usage:
    ```python
    from pipeline import Pipeline
    from pipeline.steps import PipelineStep

    # Initialize pipeline
    pipeline = Pipeline(
        export_dir="/path/to/export",
        index_url="http://localhost:8080"
    )

    # Process documents with specific steps
    pipeline.process_documents(steps={
        PipelineStep.LOAD,
        PipelineStep.SUMMARIZE,
        PipelineStep.INDEX
    })
    ```

Note:
    - Handles resource management automatically
    - Provides comprehensive error handling
    - Supports parallel processing
    - Includes monitoring and logging
"""

from .core import Pipeline
from .document_ops import DocumentOperations
from .search import SearchOperations
from .steps import PipelineStep

__all__ = ["Pipeline", "PipelineStep", "SearchOperations", "DocumentOperations"]
