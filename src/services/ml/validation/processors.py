"""Processors for ML service operations.

This module provides processor implementations for different ML service types.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from sentence_transformers import SentenceTransformer
from spacy.language import Language

from src.core.models.chunks import Chunk
from src.services.ml.validation.parameters import EmbeddingParameters, ProcessingParameters

logger = logging.getLogger(__name__)


class ProcessorStrategy(ABC):
    """Base class for processor strategies."""

    @abstractmethod
    def process_chunk(self, chunk: Chunk) -> Dict[str, Any]:
        """Process a single chunk.

        Args:
            chunk: Chunk to process

        Returns:
            Processing results
        """
        pass

    @abstractmethod
    def process_chunks(self, chunks: List[Chunk]) -> List[Dict[str, Any]]:
        """Process multiple chunks.

        Args:
            chunks: Chunks to process

        Returns:
            List of processing results
        """
        pass


class SpacyProcessor(ProcessorStrategy):
    """Processor for spaCy language models."""

    def __init__(self, model: Language, params: ProcessingParameters) -> None:
        """Initialize processor.

        Args:
            model: Loaded spaCy model
            params: Processing parameters
        """
        self._model = model
        self._params = params
        self._disable = params.disable_components or []

    def process_chunk(self, chunk: Chunk) -> Dict[str, Any]:
        """Process a single chunk with spaCy.

        Args:
            chunk: Chunk to process

        Returns:
            Processing results
        """
        doc = self._model(chunk.text, disable=self._disable)
        return {
            "tokens": [token.text for token in doc],
            "lemmas": [token.lemma_ for token in doc],
            "pos_tags": [token.pos_ for token in doc],
            "entities": [(ent.text, ent.label_) for ent in doc.ents],
        }

    def process_chunks(self, chunks: List[Chunk]) -> List[Dict[str, Any]]:
        """Process multiple chunks with spaCy.

        Args:
            chunks: Chunks to process

        Returns:
            List of processing results
        """
        return [self.process_chunk(chunk) for chunk in chunks]


class EmbeddingProcessor(ProcessorStrategy):
    """Processor for sentence transformer models."""

    def __init__(self, model: SentenceTransformer, params: EmbeddingParameters) -> None:
        """Initialize processor.

        Args:
            model: Loaded sentence transformer model
            params: Embedding parameters
        """
        self._model = model
        self._params = params

    def process_chunk(self, chunk: Chunk) -> Dict[str, Any]:
        """Generate embeddings for a single chunk.

        Args:
            chunk: Chunk to process

        Returns:
            Embedding results
        """
        embedding = self._model.encode(
            chunk.text,
            normalize_embeddings=self._params.normalize_embeddings,
        )
        return {"embedding": embedding.tolist()}

    def process_chunks(self, chunks: List[Chunk]) -> List[Dict[str, Any]]:
        """Generate embeddings for multiple chunks.

        Args:
            chunks: Chunks to process

        Returns:
            List of embedding results
        """
        texts = [chunk.text for chunk in chunks]
        embeddings = self._model.encode(
            texts,
            normalize_embeddings=self._params.normalize_embeddings,
        )
        return [{"embedding": emb.tolist()} for emb in embeddings]
