"""Strategy model definitions for text processing."""

from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar

from .base import ProcessingMetadata


T = TypeVar("T")


class ProcessingStrategy(Protocol[T]):
    """Protocol defining the interface for processing strategies.

    All processing strategies must implement this interface to ensure
    consistent behavior and interchangeability.

    Type Parameters:
        T: The type of result produced by this strategy
    """

    def process(self, content: str, metadata: dict[str, Any] | None = None) -> T:
        """Process the given content using the strategy.

        Args:
            content: The text content to process
            metadata: Optional metadata to guide processing

        Returns:
            Processed result in strategy-specific format

        Raises:
            ValueError: If content is invalid
            TypeError: If content type is incorrect
        """
        ...

    def validate(self, content: str) -> list[str]:
        """Validate input content before processing.

        Args:
            content: Content to validate

        Returns:
            List of validation error messages, empty if valid
        """
        ...


@dataclass
class StrategyResult:
    """Base class for strategy processing results.

    This class provides a common structure for strategy results,
    including metadata and error tracking.

    Attributes:
        success: Whether processing was successful
        error_message: Error message if processing failed
        metadata: Processing metadata
    """

    success: bool = True
    error_message: str | None = None
    metadata: ProcessingMetadata = field(default_factory=ProcessingMetadata)

    def validate(self) -> list[str]:
        """Validate the result.

        Returns:
            List of validation error messages, empty if valid
        """
        errors = []
        if not self.success and not self.error_message:
            errors.append("Failed results must have an error message")
        return errors


@dataclass
class TokenizationResult(StrategyResult):
    """Result from tokenization processing.

    Attributes:
        tokens: List of token strings
        token_spans: Character spans for each token
    """

    tokens: list[str] = field(default_factory=list)
    token_spans: list[tuple[int, int]] = field(default_factory=list)

    def validate(self) -> list[str]:
        """Validate the tokenization result."""
        errors = super().validate()
        if len(self.tokens) != len(self.token_spans):
            errors.append("Number of tokens must match number of spans")
        return errors


@dataclass
class NERResult(StrategyResult):
    """Result from named entity recognition.

    Attributes:
        entities: List of named entities with details
    """

    entities: list[dict[str, Any]] = field(default_factory=list)

    def validate(self) -> list[str]:
        """Validate the NER result."""
        errors = super().validate()
        for entity in self.entities:
            if "text" not in entity or "label" not in entity:
                errors.append("Each entity must have text and label")
        return errors


@dataclass
class SentimentResult(StrategyResult):
    """Result from sentiment analysis.

    Attributes:
        score: Sentiment score (-1.0 to 1.0)
        confidence: Confidence in the sentiment score
    """

    score: float = 0.0
    confidence: float = 0.0

    def validate(self) -> list[str]:
        """Validate the sentiment result."""
        errors = super().validate()
        if not -1.0 <= self.score <= 1.0:
            errors.append("Sentiment score must be between -1.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            errors.append("Confidence must be between 0.0 and 1.0")
        return errors


@dataclass
class TopicResult(StrategyResult):
    """Result from topic identification.

    Attributes:
        topic_id: Identified topic ID
        confidence: Confidence in the topic assignment
        related_topics: List of related topic IDs
    """

    topic_id: str | None = None
    confidence: float = 0.0
    related_topics: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        """Validate the topic result."""
        errors = super().validate()
        if self.success and not self.topic_id:
            errors.append("Successful results must have a topic_id")
        if not 0.0 <= self.confidence <= 1.0:
            errors.append("Confidence must be between 0.0 and 1.0")
        return errors


@dataclass
class SummaryResult(StrategyResult):
    """Result from text summarization.

    Attributes:
        summary: Generated summary text
        compression_ratio: Ratio of summary length to original text length
        key_points: List of extracted key points
    """

    summary: str = ""
    compression_ratio: float = 0.0
    key_points: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        """Validate the summary result."""
        errors = super().validate()
        if self.success and not self.summary:
            errors.append("Successful results must have a summary")
        if not 0.0 <= self.compression_ratio <= 1.0:
            errors.append("Compression ratio must be between 0.0 and 1.0")
        return errors


@dataclass
class KeywordResult(StrategyResult):
    """Result from keyword extraction.

    Attributes:
        keywords: List of extracted keywords with scores
        max_keywords: Maximum number of keywords to extract
    """

    keywords: list[dict[str, Any]] = field(default_factory=list)
    max_keywords: int = 10

    def validate(self) -> list[str]:
        """Validate the keyword result."""
        errors = super().validate()
        if self.success and not self.keywords:
            errors.append("Successful results must have keywords")
        if len(self.keywords) > self.max_keywords:
            errors.append(f"Number of keywords exceeds maximum of {self.max_keywords}")
        for keyword in self.keywords:
            if "text" not in keyword or "score" not in keyword:
                errors.append("Each keyword must have text and score")
            elif not 0.0 <= keyword["score"] <= 1.0:
                errors.append("Keyword scores must be between 0.0 and 1.0")
        return errors
