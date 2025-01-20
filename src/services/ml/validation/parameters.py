"""Parameter definitions for ML services.

This module provides parameter classes for configuring ML services and validation.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ValidationParameters:
    """Base validation parameters."""

    min_text_length: int = 10
    max_text_length: int = 1000000
    min_words: int = 3
    required_metadata_fields: Optional[set[str]] = None
    optional_metadata_fields: Optional[set[str]] = None


@dataclass
class BatchValidationParameters:
    """Parameters for batch validation."""

    max_batch_size: int = 1000
    max_memory_mb: int = 1024


@dataclass
class ServiceParameters:
    """Base parameters for ML services."""

    model_name: str
    batch_size: int = 32
    validation: ValidationParameters = ValidationParameters()
    batch: BatchValidationParameters = BatchValidationParameters()


@dataclass
class ProcessingParameters(ServiceParameters):
    """Parameters for text processing service."""

    enable_ner: bool = True
    enable_sentiment: bool = True
    enable_topics: bool = True


@dataclass
class EmbeddingParameters(ServiceParameters):
    """Parameters for embedding service."""

    device: str = "cpu"
    normalize_embeddings: bool = True
    pooling_strategy: str = "mean"
