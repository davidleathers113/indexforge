"""Text processor implementation."""

from typing import TYPE_CHECKING, Any

try:
    import nltk
    from nltk.tokenize import sent_tokenize

    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

from src.core.types.processing import ProcessingError
from src.core.types.service import ServiceState

from .base import BaseProcessor

if TYPE_CHECKING:
    from src.core.settings import Settings


class TextProcessor(BaseProcessor[list[str]]):
    """Processor for text content with sentence segmentation.

    This processor handles text normalization and sentence segmentation
    using NLTK's sentence tokenizer.

    Attributes:
        settings: Application settings
        tokenizer: NLTK sentence tokenizer
    """

    def __init__(self, settings: "Settings") -> None:
        """Initialize the processor.

        Args:
            settings: Application settings

        Raises:
            ValueError: If required settings are missing
        """
        super().__init__(settings)
        self._tokenizer = None

    async def initialize(self) -> None:
        """Initialize NLTK components.

        This method downloads required NLTK data and initializes
        the sentence tokenizer.

        Raises:
            ProcessingError: If initialization fails
        """
        self._transition_state(ServiceState.INITIALIZING)
        try:
            if not NLTK_AVAILABLE:
                raise ProcessingError(
                    "NLTK is required for text processing",
                    service_name=self.__class__.__name__,
                )

            # Download required NLTK data
            try:
                nltk.download("punkt", quiet=True)
            except Exception:
                raise ProcessingError(
                    "Failed to download NLTK data",
                    service_name=self.__class__.__name__,
                )

            # Initialize tokenizer
            self._initialize_strategies()
            self._transition_state(ServiceState.RUNNING)

            # Add initialization metadata
            self.add_metadata("nltk_version", nltk.__version__)
            self.add_metadata("tokenizer_type", "punkt")

        except Exception as e:
            self._transition_state(ServiceState.ERROR)
            if not isinstance(e, ProcessingError):
                raise ProcessingError(
                    f"Failed to initialize text processor: {e}",
                    service_name=self.__class__.__name__,
                )
            raise

    def _initialize_strategies(self) -> None:
        """Initialize text processing strategies.

        This method sets up the sentence tokenization strategy.

        Raises:
            ProcessingError: If strategy initialization fails
        """
        try:

            class SentenceTokenizer:
                def process(
                    self, content: str, metadata: dict[str, Any] | None = None
                ) -> list[str]:
                    return sent_tokenize(content)

            self.add_strategy(SentenceTokenizer())
        except Exception:
            raise ProcessingError(
                "Failed to initialize sentence tokenizer",
                service_name=self.__class__.__name__,
            )

    def process_text(self, text: str, metadata: dict[str, Any] | None = None) -> list[str]:
        """Process text into sentences.

        This method normalizes the text and splits it into sentences
        using NLTK's sentence tokenizer.

        Args:
            text: Text to process
            metadata: Optional processing metadata

        Returns:
            List of sentences

        Raises:
            ProcessingStateError: If processor is not initialized
            ValueError: If text is invalid
            TypeError: If text is not a string
        """
        self._check_running()

        # Validate input
        if not isinstance(text, str):
            raise TypeError("Input must be a string")
        if not text.strip():
            raise ValueError("Input text cannot be empty or whitespace only")

        # Add processing metadata
        if metadata:
            self.add_metadata("text_metadata", metadata)
        self.add_metadata("text_length", len(text))

        # Process with tokenizer strategy
        try:
            sentences = self._strategies[0].process(text, metadata)
            self.add_metadata("sentence_count", len(sentences))
            return sentences
        except Exception as e:
            self.add_metadata("tokenization_error", str(e))
            raise ValueError(f"Text tokenization failed: {e}")

    def process_texts(
        self, texts: list[str], metadata: dict[str, Any] | None = None
    ) -> list[list[str]]:
        """Process multiple texts into sentences.

        This method processes each text in sequence, applying
        normalization and sentence segmentation.

        Args:
            texts: Texts to process
            metadata: Optional processing metadata

        Returns:
            List of sentence lists

        Raises:
            ProcessingStateError: If processor is not initialized
            ValueError: If any text is invalid
            TypeError: If any text is not a string
        """
        self._check_running()

        # Add batch processing metadata
        if metadata:
            self.add_metadata("batch_metadata", metadata)
        self.add_metadata("batch_size", len(texts))

        processed_texts = []
        for i, text in enumerate(texts):
            try:
                sentences = self.process_text(text, metadata)
                processed_texts.append(sentences)
            except Exception as e:
                self.add_metadata("failed_text_index", i)
                raise ValueError(f"Failed to process text at index {i}: {e}")

        return processed_texts
