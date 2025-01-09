"""Models package initialization.

This package provides data models and configuration settings for various
components of the system. It includes configuration classes for document
processing, summarization, and clustering operations.

Components:
1. Summarizer Configuration:
   - Model parameters
   - Token limits
   - Generation settings
   - Chunking options

2. Clustering Configuration:
   - Cluster parameters
   - Size constraints
   - Randomization settings
   - Performance tuning

3. Configuration Management:
   - Default values
   - Validation rules
   - Type checking
   - Parameter constraints

Usage:
    ```python
    from src.models import SummarizerConfig, ClusteringConfig

    # Configure summarizer
    summarizer_config = SummarizerConfig(
        max_length=150,
        min_length=50,
        chunk_size=1024
    )

    # Configure clustering
    clustering_config = ClusteringConfig(
        n_clusters=5,
        min_cluster_size=3
    )
    ```

Note:
    - All configurations are immutable
    - Provides type hints and validation
    - Includes default values
    - Supports dataclass features
"""

from .settings import ClusteringConfig, SummarizerConfig

__all__ = ["SummarizerConfig", "ClusteringConfig"]
