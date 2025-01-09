"""Pipeline module for text summarization.

This module provides the core pipeline functionality for text summarization,
handling model initialization, text processing, and error handling. It includes:

1. Pipeline Features:
   - Model management
   - Text processing
   - Chunk handling
   - Error recovery

2. Integration:
   - Transformer models
   - Configuration
   - Resource cleanup
   - Monitoring

3. Processing:
   - Batch support
   - Length control
   - Quality settings
   - Performance tuning

Usage:
    ```python
    from transformers import pipeline
    from src.utils.summarizer.pipeline import SummarizationPipeline
    from src.utils.summarizer.config import SummarizerConfig

    # Initialize pipeline
    model = pipeline("summarization", model="t5-small")
    config = SummarizerConfig()
    summarizer = SummarizationPipeline(model, config)

    # Generate summary
    result = summarizer.generate_summary(text)
    ```

Note:
    - Uses Hugging Face models
    - Handles resource cleanup
    - Provides error handling
    - Supports configuration
"""

from .summarizer import SummarizationPipeline

__all__ = ["SummarizationPipeline"]
