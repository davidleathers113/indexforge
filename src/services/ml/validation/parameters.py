"""Parameter types for ML service validation.

This module defines parameter types used across ML services.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class BaseParameters:
    """Base parameters for all ML services."""

    min_text_length: int = 1
    max_text_length: int = 1000000
    min_words: int = 1
    required_metadata_fields: List[str] = None
    optional_metadata_fields: List[str] = None


@dataclass
class ValidationParameters:
    """Parameters for validation operations."""

    min_text_length: int = 1
    max_text_length: int = 1000000
    min_words: int = 1
    required_metadata_fields: List[str] = None
    optional_metadata_fields: List[str] = None


@dataclass
class BatchValidationParameters:
    """Parameters for batch validation."""

    max_batch_size: int = 100
    max_memory_mb: float = 1000.0


@dataclass
class ServiceParameters(BaseParameters):
    """Parameters for ML service configuration."""

    batch_size: int = 32
    max_memory_mb: float = 1000.0
    device: str = "cpu"


@dataclass
class ProcessingParameters(ServiceParameters):
    """Parameters for text processing services."""

    model_name: str = "en_core_web_sm"
    disable_components: List[str] = None


@dataclass
class EmbeddingParameters(ServiceParameters):
    """Parameters for embedding services."""

    model_name: str = "all-MiniLM-L6-v2"
    normalize_embeddings: bool = True
