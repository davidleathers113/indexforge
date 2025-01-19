"""
Configuration builder for Weaviate schemas.

This module provides a builder class for creating various Weaviate schema
configurations, including vectorizer settings, vector index parameters,
and BM25 configurations.

Example:
    ```python
    from src.indexing.schema.configuration_builder import ConfigurationBuilder

    # Create vectorizer configuration
    vectorizer_config = ConfigurationBuilder.vectorizer_config(
        "text2vec-transformers",
        model="sentence-transformers/all-mpnet-base-v2",
        pooling="masked_mean",
    )

    # Create vector index configuration
    vector_index_config = ConfigurationBuilder.vector_index_config(
        distance="cosine",
        ef=200,
        max_connections=128,
    )

    # Create BM25 configuration
    bm25_config = ConfigurationBuilder.bm25_config(b=0.75, k1=1.2)
    ```
"""

from typing import Any


class ConfigurationBuilder:
    """
    Builder class for Weaviate schema configurations.

    This class provides static methods for creating various configuration
    objects used in Weaviate schemas. Each method returns a dictionary
    with the appropriate configuration structure.

    Example:
        ```python
        # Create vectorizer configuration
        vectorizer_config = ConfigurationBuilder.vectorizer_config(
            "text2vec-transformers",
            model="sentence-transformers/all-mpnet-base-v2",
        )

        # Create vector index configuration
        vector_index_config = ConfigurationBuilder.vector_index_config(
            distance="cosine",
            ef=100,
        )
        ```
    """

    @staticmethod
    def vectorizer_config(
        vectorizer: str,
        model: str | None = None,
        pooling: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create a vectorizer configuration.

        Args:
            vectorizer (str): Vectorizer name (e.g., "text2vec-transformers")
            model (Optional[str]): Model name for transformers
            pooling (Optional[str]): Pooling strategy
            **kwargs: Additional configuration options

        Returns:
            Dict[str, Any]: Vectorizer configuration dictionary

        Example:
            ```python
            config = ConfigurationBuilder.vectorizer_config(
                "text2vec-transformers",
                model="sentence-transformers/all-mpnet-base-v2",
                pooling="masked_mean",
                truncation=True,
            )
            ```
        """
        return {
            "vectorizer": vectorizer,
            "moduleConfig": {
                vectorizer: {
                    **({"model": model} if model else {}),
                    **({"poolingStrategy": pooling} if pooling else {}),
                    **kwargs,
                }
            },
        }

    @staticmethod
    def vector_index_config(
        distance: str = "cosine",
        ef: int = 100,
        max_connections: int = 64,
        dynamic_ef_min: int | None = None,
        dynamic_ef_max: int | None = None,
        dynamic_ef_factor: float | None = None,
        vector_cache_max_objects: int | None = None,
        cleanup_interval_seconds: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create a vector index configuration.

        Args:
            distance (str): Distance metric (default: "cosine")
            ef (int): Size of the dynamic list for searching (default: 100)
            max_connections (int): Maximum number of connections (default: 64)
            dynamic_ef_min (Optional[int]): Minimum ef value
            dynamic_ef_max (Optional[int]): Maximum ef value
            dynamic_ef_factor (Optional[float]): Factor for dynamic ef
            vector_cache_max_objects (Optional[int]): Maximum cached vectors
            cleanup_interval_seconds (Optional[int]): Cleanup interval
            **kwargs: Additional configuration options

        Returns:
            Dict[str, Any]: Vector index configuration dictionary

        Example:
            ```python
            config = ConfigurationBuilder.vector_index_config(
                distance="cosine",
                ef=200,
                max_connections=128,
                dynamic_ef_factor=8,
            )
            ```
        """
        config = {
            "distance": distance,
            "ef": ef,
            "maxConnections": max_connections,
        }

        if dynamic_ef_min is not None:
            config["dynamicEfMin"] = dynamic_ef_min
        if dynamic_ef_max is not None:
            config["dynamicEfMax"] = dynamic_ef_max
        if dynamic_ef_factor is not None:
            config["dynamicEfFactor"] = dynamic_ef_factor
        if vector_cache_max_objects is not None:
            config["vectorCacheMaxObjects"] = vector_cache_max_objects
        if cleanup_interval_seconds is not None:
            config["cleanupIntervalSeconds"] = cleanup_interval_seconds

        return {**config, **kwargs}

    @staticmethod
    def bm25_config(
        b: float = 0.75,
        k1: float = 1.2,
    ) -> dict[str, Any]:
        """
        Create a BM25 configuration.

        Args:
            b (float): Document length normalization (default: 0.75)
            k1 (float): Term frequency saturation (default: 1.2)

        Returns:
            Dict[str, Any]: BM25 configuration dictionary

        Example:
            ```python
            config = ConfigurationBuilder.bm25_config(b=0.8, k1=1.5)
            ```
        """
        return {
            "bm25": {
                "b": b,
                "k1": k1,
            }
        }
