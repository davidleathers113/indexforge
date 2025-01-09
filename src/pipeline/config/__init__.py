"""Pipeline configuration package for managing processing settings.

This package provides configuration management for the document processing pipeline,
including settings for file paths, service connections, processing parameters, and
component-specific configurations. It uses dataclasses to ensure type safety and
provide default values for optional settings.

Classes:
    PipelineConfig: Main configuration class for pipeline settings

Example:
    ```python
    from src.pipeline.config import PipelineConfig

    # Create configuration with custom settings
    config = PipelineConfig(
        export_dir="path/to/exports",
        index_url="http://localhost:8080",
        batch_size=200,
        cache_ttl=3600,
        max_document_length=16384
    )

    # Access configuration settings
    print(f"Export directory: {config.export_dir}")
    print(f"Batch size: {config.batch_size}")
    print(f"Cache TTL: {config.cache_ttl} seconds")

    # Use configuration in pipeline
    from src.pipeline import Pipeline
    pipeline = Pipeline(config)
    ```

Note:
    Configuration values are validated during initialization, and paths are
    automatically converted to the appropriate type. The configuration is
    immutable after creation to ensure consistency during pipeline execution.
"""

from .settings import PipelineConfig

__all__ = ["PipelineConfig"]
