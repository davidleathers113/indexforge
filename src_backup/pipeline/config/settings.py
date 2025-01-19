"""Pipeline configuration settings.

This module defines the configuration settings for the document processing pipeline.
It provides a dataclass-based configuration that handles all necessary settings
for the pipeline components, including paths, connection details, and processing
parameters.

Classes:
    PipelineConfig: Configuration dataclass for pipeline settings.

Example:
    ```python
    config = PipelineConfig(
        export_dir="path/to/exports",
        index_url="http://localhost:8080",
        batch_size=200
    )
    ```
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PipelineConfig:
    """Configuration settings for the document processing pipeline.

    This dataclass encapsulates all configuration parameters needed for the pipeline,
    including file system paths, connection settings for various services, and
    document processing parameters. It provides automatic path conversion and
    validation through its post-initialization hook.

    Attributes:
        export_dir (Path): Directory containing the documents to process
        index_url (str): URL of the vector index service. Defaults to "http://localhost:8080"
        log_dir (Path): Directory for storing log files. Defaults to "logs"
        batch_size (int): Number of documents to process in each batch. Defaults to 100
        class_name (str): Name of the document class in the vector index. Defaults to "Document"
        cache_host (str): Redis cache host address. Defaults to "localhost"
        cache_port (int): Redis cache port number. Defaults to 6379
        cache_ttl (int): Cache TTL in seconds. Defaults to 86400 (24 hours)
        min_document_length (int): Minimum length of documents to process. Defaults to 50
        max_document_length (int): Maximum length of documents to process. Defaults to 8192
        max_retries (int): Maximum number of retry attempts for failed operations. Defaults to 3

    Example:
        ```python
        config = PipelineConfig(
            export_dir="documents",
            batch_size=200,
            max_document_length=16384
        )

        # Access configuration
        print(f"Processing documents from {config.export_dir}")
        print(f"Using batch size of {config.batch_size}")
        ```
    """

    export_dir: Path
    index_url: str = "http://localhost:8080"
    log_dir: Path = Path("logs")
    batch_size: int = 100
    class_name: str = "Document"
    cache_host: str = "localhost"
    cache_port: int = 6379
    cache_ttl: int = 86400
    min_document_length: int = 50
    max_document_length: int = 8192
    max_retries: int = 3

    def __post_init__(self):
        """Validate and convert path attributes.

        This method is automatically called after instance initialization to ensure
        that path-related attributes are properly converted to Path objects. It
        handles both string and Path inputs for path-related fields.

        Raises:
            TypeError: If a path-related attribute cannot be converted to a Path object
        """
        if isinstance(self.export_dir, str):
            self.export_dir = Path(self.export_dir)
        if isinstance(self.log_dir, str):
            self.log_dir = Path(self.log_dir)
