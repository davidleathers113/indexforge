"""Core module for text summarization processing.

This module provides the main document processing functionality for text
summarization, including resource management and pipeline control. It includes:

1. Document Processing:
   - Text extraction
   - Batch handling
   - Resource management
   - Error handling

2. Pipeline Control:
   - Model initialization
   - Configuration
   - Cleanup
   - Monitoring

3. Integration:
   - Cache support
   - Logging
   - Error tracking
   - Performance metrics

Usage:
    ```python
    from src.utils.summarizer.core import DocumentSummarizer
    from src.utils.summarizer.config import SummarizerConfig

    # Initialize processor
    config = SummarizerConfig()
    processor = DocumentSummarizer(config)

    # Process documents
    docs = [doc1, doc2, doc3]
    results = processor.process_documents(docs)
    ```

Note:
    - Manages model resources
    - Supports batch processing
    - Handles cleanup
    - Provides monitoring
"""

from .processor import DocumentSummarizer

__all__ = ["DocumentSummarizer"]
