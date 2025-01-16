"""Embedding generator module for document vectorization.

This module provides functionality for generating embeddings from document text using OpenAI's
embedding models. It supports text chunking, caching, and both body and summary embeddings
generation with configurable parameters.
"""

import logging

import numpy as np
from openai import OpenAI

from src.utils.cache_manager import CacheManager
from src.utils.chunking import ChunkingConfig


logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates and manages document embeddings using OpenAI's API.

    This class handles the generation of vector embeddings for documents, including
    text chunking, caching, and normalization. It supports both full document and
    summary embeddings, with configurable model parameters and caching options.

    Attributes:
        model (str): The OpenAI model identifier for generating embeddings.
        dimensions (Optional[int]): Number of dimensions for the embedding vectors.
        chunking_config (ChunkingConfig): Configuration for text chunking.
        client (OpenAI): OpenAI client instance for API calls.
        cache_manager (CacheManager): Manager for caching embeddings.
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        dimensions: int | None = None,
        cache_manager: CacheManager | None = None,
        cache_host: str = "localhost",
        cache_port: int = 6379,
        cache_ttl: int = 86400,
        client: OpenAI | None = None,
    ):
        """Initialize the embedding generator with specified configuration.

        Args:
            model: OpenAI model identifier for embeddings (default: "text-embedding-3-small").
            chunk_size: Maximum number of tokens per text chunk (default: 512).
            chunk_overlap: Number of overlapping tokens between chunks (default: 50).
            dimensions: Optional fixed dimensionality for embeddings.
            cache_manager: Optional pre-configured cache manager instance.
            cache_host: Redis cache host address (default: "localhost").
            cache_port: Redis cache port number (default: 6379).
            cache_ttl: Cache time-to-live in seconds (default: 86400).
            client: Optional pre-configured OpenAI client instance.

        Example:
            ```python
            generator = EmbeddingGenerator(
                model="text-embedding-3-small",
                chunk_size=512,
                dimensions=1536,
                cache_host="redis.example.com"
            )
            ```
        """
        logger.info(f"Initializing EmbeddingGenerator with model={model}, chunk_size={chunk_size}")
        self.model = model
        self.dimensions = dimensions
        try:
            self.chunking_config = ChunkingConfig(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                model_name="cl100k_base",
                max_chunk_size=chunk_size * 4,
            )
            logger.debug(f"Created chunking config: {self.chunking_config}")
        except Exception as e:
            logger.error(f"Failed to create chunking config: {e!s}")
            raise

        self.client = client or OpenAI()
        self.cache_manager = cache_manager or CacheManager(
            host=cache_host,
            port=cache_port,
            prefix="emb",
            default_ttl=cache_ttl,
        )
        logger.info("EmbeddingGenerator initialization complete")

    def _normalize_l2(self, x: list[float] | np.ndarray) -> np.ndarray:
        """Perform L2 normalization on embedding vectors.

        Normalizes input vectors to have unit L2 norm (Euclidean length = 1), which is
        standard practice for embedding vectors to ensure consistent scaling in the
        embedding space. This is particularly important for:
        - Cosine similarity calculations
        - Nearest neighbor searches
        - Embedding space operations

        The normalization process:
        1. Converts input to float64 for consistent precision
        2. Computes L2 norm (Euclidean length)
        3. Divides each vector by its norm
        4. Handles zero vectors by returning them unchanged

        Args:
            x: Input vector or matrix to normalize. Can be:
               - Single vector: shape (d,) where d is dimensionality
               - Matrix: shape (n, d) where n is number of vectors

        Returns:
            np.ndarray: L2-normalized vector(s) with unit length.
                       Same shape as input but with float64 precision.

        Note:
            - Zero vectors are returned unchanged to avoid division by zero
            - For matrices, normalization is applied to each row independently
            - Results are cached for consistent normalization across calls
        """
        x = np.array(x, dtype=np.float64)  # Ensure consistent float64 precision
        if x.ndim == 1:
            # Cache the norm for single vectors
            norm = np.linalg.norm(x)
            if norm == 0:
                return x
            normalized = x / norm
            return normalized
        else:
            # Cache the norms for matrices
            norms = np.linalg.norm(x, axis=1, keepdims=True)
            # Handle zero vectors while maintaining float64 precision
            normalized = np.divide(x, norms, out=x.copy(), where=norms != 0)
            return normalized

    def _get_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text segment.

        Makes an API call to OpenAI to generate an embedding vector for the given text,
        with optional normalization if dimensions are specified.

        Args:
            text: Input text to generate embedding for.

        Returns:
            List[float]: Generated embedding vector.

        Raises:
            Exception: If embedding generation fails or API call errors occur.

        Example:
            ```python
            embedding = generator._get_embedding("Sample text for embedding")
            ```
        """
        try:
            if not isinstance(text, str):
                raise ValueError("Invalid input type: text must be a string")

            logger.debug(f"Generating embedding for text of length {len(text)}")
            response = self.client.embeddings.create(
                model=self.model, input=text, dimensions=self.dimensions, encoding_format="float"
            )
            embedding = response.data[0].embedding
            logger.debug(f"Generated raw embedding of length {len(embedding)}")

            if self.dimensions:
                logger.debug(f"Normalizing embedding to {self.dimensions} dimensions")
                embedding = self._normalize_l2(embedding).tolist()
                logger.debug("Normalization complete")

            return embedding

        except Exception as e:
            error_msg = f"Error generating embedding: {e!s}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg) from e

    def cleanup(self):
        """Clean up resources used by the embedding generator.

        Performs cleanup operations including:
        - Closing the cache manager connection
        - Cleaning up the OpenAI client
        - Logging cleanup status

        Raises:
            Exception: If cleanup operations fail.
        """
        try:
            if self.cache_manager:
                self.cache_manager.cleanup()

            if hasattr(self, "client"):
                self.client.close()

            logger.info("EmbeddingGenerator resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e!s}")
            raise

    def generate_embeddings(self, documents: list[dict]) -> list[dict]:
        """Generate embeddings for a batch of documents.

        Processes a list of documents, generating embeddings for both body text and
        summaries. Handles text chunking, embedding generation, and error cases.

        Args:
            documents: List of document dictionaries containing content and metadata.

        Returns:
            List[Dict]: Documents with added embedding information including:
                - body: Main content embedding
                - summary: Optional summary embedding
                - version: Embedding version identifier
                - model: Model used for generation
                - chunks: Optional chunk information if text was split

        Raises:
            ValueError: If a document has no body text.
            Exception: For embedding generation failures.

        Example:
            ```python
            docs = [
                {
                    "content": {
                        "body": "Main document text",
                        "summary": "Document summary"
                    },
                    "embeddings": {}
                }
            ]
            processed_docs = generator.generate_embeddings(docs)
            ```
        """
        processed_docs = []
        logger.info(f"Processing {len(documents)} documents")

        for doc in documents:
            try:
                # Process body text
                body_text = doc["content"].get("body", "")
                if not body_text:
                    logger.warning("Document has no body text")
                    raise ValueError("Document has no body text")

                # Generate embeddings for body chunks
                from src.utils.chunking.base import chunk_text_by_tokens

                logger.debug(f"Chunking text of length {len(body_text)}")
                try:
                    chunks = chunk_text_by_tokens(body_text, self.chunking_config)
                    logger.debug(f"Created {len(chunks)} chunks")
                except Exception as e:
                    logger.error(f"Failed to chunk text: {e!s}, config={self.chunking_config}")
                    raise

                chunk_embeddings = []
                failed_chunks = 0

                # Try to generate embeddings for each chunk
                for i, chunk in enumerate(chunks):
                    try:
                        logger.debug(f"Processing chunk {i + 1}/{len(chunks)} of length {len(chunk)}")
                        embedding = self._get_embedding(chunk)
                        chunk_embeddings.append(embedding)
                    except Exception as e:
                        logger.error(f"Failed to generate embedding for chunk {i + 1}: {e!s}")
                        failed_chunks += 1

                if failed_chunks == len(chunks):
                    logger.error("All chunks failed embedding generation")
                    raise Exception("Failed to generate embeddings for all chunks")

                # Average chunk embeddings if multiple chunks
                logger.debug(f"Averaging {len(chunk_embeddings)} chunk embeddings")
                if chunk_embeddings:
                    # Convert to numpy array and ensure float64 precision
                    embeddings_array = np.array(chunk_embeddings, dtype=np.float64)
                    # Normalize each chunk embedding
                    normalized_embeddings = self._normalize_l2(embeddings_array)
                    # Average the normalized embeddings
                    body_embedding = np.mean(normalized_embeddings, axis=0).tolist()
                else:
                    body_embedding = []

                # Process summary if available
                summary_text = doc["content"].get("summary")
                try:
                    summary_embedding = self._get_embedding(summary_text) if summary_text else None
                    if summary_embedding:
                        logger.debug("Generated summary embedding")
                except Exception as e:
                    logger.error(f"Failed to generate summary embedding: {e!s}")
                    summary_embedding = None

                # Update document with embeddings
                doc["embeddings"].update(
                    {
                        "body": body_embedding,
                        "summary": summary_embedding,
                        "version": "v1",
                        "model": self.model,
                        "chunks": (
                            {"texts": chunks, "vectors": chunk_embeddings}
                            if len(chunks) > 1
                            else None
                        ),
                    }
                )
                logger.info("Successfully processed document")

            except Exception as e:
                logger.error(f"Error processing document: {e!s}", exc_info=True)
                doc["embeddings"].update(
                    {
                        "body": [],
                        "summary": None,
                        "version": "v1_failed",
                        "model": self.model,
                        "error": f"Failed to generate embeddings: {e!s}",
                    }
                )

            processed_docs.append(doc)

        logger.info(f"Completed processing {len(documents)} documents")
        return processed_docs
