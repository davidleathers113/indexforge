"""NLP-based processing strategies."""

from typing import Any

from spacy.language import Language
from spacy.tokens import Doc

from src.ml.processing.types import ProcessingStrategy


class TokenizationStrategy(ProcessingStrategy[list[str]]):
    """Strategy for text tokenization using spaCy.

    This strategy handles text tokenization and basic linguistic
    analysis using spaCy's language models.

    Attributes:
        nlp: spaCy language model
    """

    def __init__(self, nlp: Language) -> None:
        """Initialize the strategy.

        Args:
            nlp: Initialized spaCy language model
        """
        self.nlp = nlp

    def process(self, content: str, metadata: dict[str, Any] | None = None) -> list[str]:
        """Process text content into tokens.

        Args:
            content: Text content to process
            metadata: Optional processing metadata

        Returns:
            List of token strings

        Raises:
            ValueError: If content is invalid
        """
        if not content:
            raise ValueError("Content cannot be empty")

        doc: Doc = self.nlp(content)
        return [token.text for token in doc]


class NERStrategy(ProcessingStrategy[list[dict[str, Any]]]):
    """Strategy for named entity recognition using spaCy.

    This strategy identifies and classifies named entities
    in text using spaCy's NER models.

    Attributes:
        nlp: spaCy language model
    """

    def __init__(self, nlp: Language) -> None:
        """Initialize the strategy.

        Args:
            nlp: Initialized spaCy language model
        """
        self.nlp = nlp

    def process(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Process text content to extract named entities.

        Args:
            content: Text content to process
            metadata: Optional processing metadata

        Returns:
            List of entity dictionaries with text, label, and position

        Raises:
            ValueError: If content is invalid
        """
        if not content:
            raise ValueError("Content cannot be empty")

        doc: Doc = self.nlp(content)
        return [
            {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
            }
            for ent in doc.ents
        ]


class SentimentStrategy(ProcessingStrategy[float]):
    """Strategy for sentiment analysis using spaCy.

    This strategy analyzes the sentiment of text content
    using spaCy's linguistic features.

    Attributes:
        nlp: spaCy language model
    """

    def __init__(self, nlp: Language) -> None:
        """Initialize the strategy.

        Args:
            nlp: Initialized spaCy language model
        """
        self.nlp = nlp

    def process(self, content: str, metadata: dict[str, Any] | None = None) -> float:
        """Process text content to determine sentiment.

        Args:
            content: Text content to process
            metadata: Optional processing metadata

        Returns:
            Sentiment score between -1.0 and 1.0

        Raises:
            ValueError: If content is invalid
        """
        if not content:
            raise ValueError("Content cannot be empty")

        # Simple example - replace with actual sentiment analysis
        doc: Doc = self.nlp(content)
        # Placeholder implementation
        return 0.0  # Neutral sentiment
