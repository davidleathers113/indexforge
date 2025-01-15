"""
Provides classes and utilities for processing and representing search results.

This module contains the core classes for handling search results from the Weaviate
vector database. It includes the SearchResult dataclass for representing individual
search results and the ResultProcessor class for processing raw search responses.

The module handles result validation, data extraction, and proper error logging
to ensure robust processing of search results in production environments.

Example:
    ```python
    # Process raw search results from Weaviate
    processor = ResultProcessor()
    results = processor.process_results(raw_weaviate_response)

    # Access processed results
    for result in results:
        print(f"Document {result.id}:")
        print(f"Title: {result.content.get('title')}")
        print(f"Score: {result.score}")
    ```
"""

from dataclasses import dataclass
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """
    A dataclass representing a processed search result from Weaviate.

    This class encapsulates all relevant information about a search result,
    including its content, metadata, and search-specific metrics like score
    and distance.

    Attributes:
        id: Unique identifier of the document
        content: Dictionary containing document content (body, title, summary)
        metadata: Dictionary containing document metadata (timestamp, version, etc.)
        score: Similarity score from the search operation (0-1)
        distance: Optional distance metric from vector comparison
        vector: Optional vector embedding of the document

    Example:
        ```python
        result = SearchResult(
            id="doc123",
            content={"title": "Example", "body": "Content..."},
            metadata={"timestamp": "2023-01-01", "version": "1.0"},
            score=0.95
        )
        print(f"Document {result.id} matched with score {result.score}")
        ```
    """

    id: str
    content: Dict
    metadata: Dict
    score: float
    distance: Optional[float] = None
    vector: Optional[List[float]] = None

    @classmethod
    def from_weaviate_result(cls, result: Dict) -> "SearchResult":
        """
        Create a SearchResult instance from a raw Weaviate response.

        This method processes a raw result dictionary from Weaviate and extracts
        all relevant information into a structured SearchResult instance. It handles
        missing or malformed data gracefully with appropriate logging.

        Args:
            result: Raw result dictionary from Weaviate containing _additional field
                   with id, score, and optional vector, plus content and metadata

        Returns:
            SearchResult: A processed search result instance

        Raises:
            KeyError: If critical fields are missing from the result
            ValueError: If result data is malformed or invalid

        Example:
            ```python
            raw_result = {
                "_additional": {"id": "doc123", "score": 0.95},
                "content": {"title": "Example", "body": "Content..."},
                "metadata": {"timestamp": "2023-01-01"}
            }
            result = SearchResult.from_weaviate_result(raw_result)
            ```
        """
        logger.debug(f"Processing raw search result: {result.get('_additional', {}).get('id')}")
        additional = result.get("_additional", {})

        # Log important metrics
        score = additional.get("score", 0.0)
        distance = additional.get("distance")
        logger.debug(
            f"Result metrics - ID: {additional.get('id')}, Score: {score}, Distance: {distance}"
        )

        # Check for required fields
        if not additional.get("id"):
            logger.warning("Search result missing required 'id' field")
        if "score" not in additional:
            logger.warning("Search result missing 'score' field")

        # Extract content and metadata
        content = result.get("content", {})
        if not content:
            logger.warning("Search result missing content")
            content = {
                "body": result.get("content_body", ""),
                "summary": result.get("content_summary", ""),
                "title": result.get("content_title", ""),
            }

        metadata = result.get("metadata", {})
        if not metadata:
            logger.warning("Search result missing metadata, constructing from fields")
            metadata = {
                "timestamp_utc": result.get("timestamp_utc"),
                "schema_version": result.get("schema_version"),
                "parent_id": result.get("parent_id"),
                "chunk_ids": result.get("chunk_ids", []),
            }

        # Create instance
        instance = cls(
            id=additional.get("id"),
            content=content,
            metadata=metadata,
            score=score,
            distance=distance,
            vector=additional.get("vector"),
        )

        logger.debug(f"Created SearchResult instance with ID: {instance.id}")
        return instance


class ResultProcessor:
    """
    Processes raw search results from Weaviate into structured SearchResult objects.

    This class provides utilities for handling raw search responses from Weaviate,
    including result validation, error handling, and conversion to SearchResult
    instances. It includes comprehensive logging for monitoring and debugging.

    Example:
        ```python
        processor = ResultProcessor()
        raw_results = {
            "data": {
                "Get": {
                    "Document": [
                        {
                            "_additional": {"id": "doc123", "score": 0.95},
                            "content": {"title": "Example"}
                        }
                    ]
                }
            }
        }
        processed_results = processor.process_results(raw_results)
        ```
    """

    @staticmethod
    def process_results(raw_results: Dict) -> List[SearchResult]:
        """
        Process a raw search response from Weaviate into SearchResult objects.

        This method handles the complete processing pipeline for search results,
        including data validation, error handling, and conversion to SearchResult
        instances. It processes results individually to ensure partial success
        in case of individual result failures.

        Args:
            raw_results: Dictionary containing the raw Weaviate search response
                        with the expected structure: data.Get.Document[...]

        Returns:
            List[SearchResult]: List of successfully processed search results.
                              Returns empty list if processing fails entirely.

        Raises:
            Exception: If the entire processing pipeline fails. Individual result
                      failures are logged but don't raise exceptions.

        Example:
            ```python
            processor = ResultProcessor()
            try:
                results = processor.process_results(raw_weaviate_response)
                print(f"Successfully processed {len(results)} results")
            except Exception as e:
                print(f"Failed to process results: {e}")
            ```
        """
        logger.info("Processing search results")
        results = []
        try:
            documents = raw_results.get("data", {}).get("Get", {}).get("Document", [])
            logger.debug(f"Found {len(documents)} documents to process")

            for doc in documents:
                try:
                    result = SearchResult.from_weaviate_result(doc)
                    results.append(result)
                except Exception as e:
                    logger.error(
                        f"Error processing individual result: {str(e)}",
                        exc_info=True,
                        extra={"document": doc},
                    )

            logger.info(f"Successfully processed {len(results)} search results")
            if len(results) != len(documents):
                logger.warning(
                    f"Some results failed to process: {len(documents) - len(results)} failures"
                )

        except Exception as e:
            logger.error(
                f"Error processing search results: {str(e)}",
                exc_info=True,
                extra={"raw_results": raw_results},
            )

        return results
