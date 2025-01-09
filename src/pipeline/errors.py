"""Pipeline error definitions.

This module defines the hierarchy of exceptions used throughout the pipeline
system. It provides specific error types for different failure scenarios,
enabling precise error handling and reporting.

Error Hierarchy:
1. PipelineError (base class)
   ├── ValidationError
   │   - Parameter validation failures
   │   - Configuration issues
   │   - Input validation errors
   │
   ├── DirectoryError
   │   - Missing directories
   │   - Permission issues
   │   - Path resolution errors
   │
   ├── ComponentError
   │   - Component initialization failures
   │   - Integration issues
   │   - Component state errors
   │
   ├── ConfigurationError
   │   - Invalid settings
   │   - Missing configuration
   │   - Incompatible options
   │
   ├── ProcessingError
   │   ├── EmbeddingError
   │   │   - Embedding generation failures
   │   │   - Model loading issues
   │   │   - Dimension mismatches
   │   │
   │   ├── SummaryError
   │   │   - Summarization failures
   │   │   - Model errors
   │   │   - Token limit issues
   │   │
   │   ├── ClusteringError
   │   │   - Clustering algorithm failures
   │   │   - Data format issues
   │   │   - Memory constraints
   │   │
   │   └── PIIError
   │       - PII detection failures
   │       - Pattern matching errors
   │       - Redaction issues
   │
   ├── IndexingError
   │   - Index connection failures
   │   - Storage errors
   │   - Query failures
   │
   ├── LoaderError
   │   - File loading failures
   │   - Format errors
   │   - Parsing issues
   │
   ├── ResourceError
   │   - Resource allocation failures
   │   - Connection issues
   │   - Timeout errors
   │
   ├── CleanupError
   │   - Resource cleanup failures
   │   - State persistence errors
   │   - Memory leaks
   │
   └── DocumentOperationError
       - Document update failures
       - Deletion errors
       - Version conflicts

Usage:
    ```python
    from pipeline.errors import ValidationError, ProcessingError

    try:
        pipeline.process_documents()
    except ValidationError as e:
        print(f"Configuration error: {e}")
    except ProcessingError as e:
        print(f"Processing failed: {e}")
    ```

Note:
    - All errors include descriptive messages
    - Errors can wrap original exceptions
    - Stack traces are preserved
    - Logging integration is supported
"""


class PipelineError(Exception):
    """Base class for pipeline-specific errors.

    Provides common functionality for all pipeline errors:
    - Formatted error messages
    - Original error preservation
    - Stack trace handling
    """

    def __init__(self, message: str, *args):
        """Initialize error with message.

        Args:
            message: Error message format string
            *args: Format arguments for the message
        """
        if args:
            message = message % args
        super().__init__(message)


class ValidationError(PipelineError):
    """Error raised when there are validation issues.

    Used for:
    - Parameter validation failures
    - Configuration validation errors
    - Input data validation issues
    """

    pass


class DirectoryError(PipelineError):
    """Error raised when there are issues with directories.

    Used for:
    - Missing directory errors
    - Permission issues
    - Path resolution failures
    """

    pass


class ComponentError(PipelineError):
    """Error raised when there are issues with pipeline components.

    Used for:
    - Component initialization failures
    - Integration errors
    - Component state issues
    """

    pass


class ConfigurationError(PipelineError):
    """Error raised when there are issues with pipeline configuration.

    Used for:
    - Invalid configuration settings
    - Missing required configuration
    - Incompatible options
    """

    pass


class ProcessingError(PipelineError):
    """Error raised when there are issues processing documents.

    Used for:
    - Document processing failures
    - Content extraction errors
    - Format conversion issues
    """

    pass


class EmbeddingError(ProcessingError):
    """Error raised when there are issues generating embeddings.

    Used for:
    - Embedding generation failures
    - Model loading errors
    - Dimension mismatch issues
    """

    pass


class SummaryError(ProcessingError):
    """Error raised when there are issues generating summaries.

    Used for:
    - Summarization failures
    - Model errors
    - Token limit issues
    """

    pass


class ClusteringError(ProcessingError):
    """Error raised when there are issues clustering documents.

    Used for:
    - Clustering algorithm failures
    - Data format issues
    - Memory constraints
    """

    pass


class PIIError(ProcessingError):
    """Error raised when there are issues detecting PII.

    Used for:
    - PII detection failures
    - Pattern matching errors
    - Redaction issues
    """

    pass


class IndexingError(PipelineError):
    """Error raised when there are issues indexing documents.

    Used for:
    - Index connection failures
    - Storage errors
    - Query failures
    """

    pass


class LoaderError(PipelineError):
    """Error raised when there are issues loading documents.

    Used for:
    - File loading failures
    - Format errors
    - Parsing issues
    """

    pass


class ResourceError(PipelineError):
    """Error raised when there are issues with resources.

    Used for:
    - Resource allocation failures
    - Connection issues
    - Timeout errors
    """

    pass


class CleanupError(PipelineError):
    """Error raised when there are issues during cleanup.

    Used for:
    - Resource cleanup failures
    - State persistence errors
    - Memory leaks
    """

    pass


class DocumentOperationError(PipelineError):
    """Error raised when document operations fail.

    Used for:
    - Document update failures
    - Deletion errors
    - Version conflicts
    """

    pass
