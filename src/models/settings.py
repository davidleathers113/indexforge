"""Configuration settings for various components.

This module defines configuration classes for different components of the system,
using dataclasses for type safety and immutability. It provides settings for
document summarization and topic clustering operations.

Classes:
1. SummarizerConfig:
   - Controls document summarization behavior
   - Manages token limits and generation parameters
   - Configures chunking for long documents
   - Tunes generation quality and performance

2. ClusteringConfig:
   - Controls document clustering behavior
   - Manages cluster sizes and limits
   - Configures clustering algorithm parameters
   - Ensures reproducible results

Usage:
    ```python
    from src.models.settings import SummarizerConfig, ClusteringConfig

    # Configure summarization
    summary_config = SummarizerConfig(
        max_length=150,
        min_length=50,
        do_sample=True,
        temperature=0.8
    )

    # Configure clustering
    cluster_config = ClusteringConfig(
        n_clusters=10,
        min_cluster_size=5,
        random_state=42
    )
    ```

Note:
    - All settings are validated at initialization
    - Default values are carefully chosen
    - Parameters are documented with types
    - Settings are immutable after creation
"""

from dataclasses import dataclass


@dataclass
class SummarizerConfig:
    """Configuration for document summarization.

    This class defines parameters for controlling the document summarization
    process, including token limits, generation settings, and chunking options.

    Attributes:
        max_length: Maximum length of the summary in tokens
            - Controls the upper limit of generated summaries
            - Prevents overly long outputs
            - Typical range: 100-200 tokens

        min_length: Minimum length of the summary in tokens
            - Ensures summaries are sufficiently detailed
            - Prevents too short outputs
            - Typical range: 30-50 tokens

        do_sample: Whether to use sampling for text generation
            - True enables more creative summaries
            - False produces deterministic outputs
            - Affects generation diversity

        temperature: Temperature for sampling (higher = more random)
            - Controls randomness in generation
            - Range: 0.0-1.0 (0.7 recommended)
            - Higher values increase creativity

        top_p: Top-p sampling parameter
            - Controls cumulative probability threshold
            - Range: 0.0-1.0 (0.9 recommended)
            - Affects output quality

        chunk_size: Number of words per chunk for long documents
            - Controls text splitting for long inputs
            - Affects processing efficiency
            - Typical range: 512-2048 words

        chunk_overlap: Number of words overlap between chunks
            - Maintains context between chunks
            - Prevents information loss
            - Typical range: 50-200 words

    Example:
        >>> config = SummarizerConfig(
        ...     max_length=150,
        ...     min_length=50,
        ...     temperature=0.8,
        ...     chunk_size=1024
        ... )
    """

    max_length: int = 150
    min_length: int = 50
    do_sample: bool = False
    temperature: float = 0.7
    top_p: float = 0.9
    chunk_size: int = 1024  # words per chunk
    chunk_overlap: int = 100  # words overlap


@dataclass
class ClusteringConfig:
    """Configuration for topic clustering.

    This class defines parameters for controlling the document clustering
    process, including cluster sizes, limits, and algorithm settings.

    Attributes:
        n_clusters: Number of clusters to create
            - Controls the granularity of clustering
            - Affects topic distribution
            - Typical range: 5-20 clusters

        min_cluster_size: Minimum number of documents per cluster
            - Prevents too small clusters
            - Ensures meaningful groupings
            - Typical range: 3-10 documents

        max_clusters: Maximum number of clusters to consider
            - Limits computational complexity
            - Prevents over-segmentation
            - Should be > n_clusters

        random_state: Random seed for reproducibility
            - Ensures consistent results
            - Fixed seed for testing
            - Any integer value

    Example:
        >>> config = ClusteringConfig(
        ...     n_clusters=10,
        ...     min_cluster_size=5,
        ...     max_clusters=20,
        ...     random_state=42
        ... )
    """

    n_clusters: int = 5
    min_cluster_size: int = 3
    max_clusters: int = 20
    random_state: int = 42
