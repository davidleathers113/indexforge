"""Chunk processor implementation."""

from typing import TYPE_CHECKING, Any

try:
    import spacy
    from spacy.language import Language

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

from src.core.models.chunks import Chunk
from src.core.models.documents import DocumentStatus, ProcessingStep
from src.core.settings import Settings
from src.ml.service import ServiceInitializationError, ServiceState

from .base import BaseProcessor
from .errors import ValidationError
from .models.chunks import ProcessedChunk
from .results.aggregator import ResultAggregator
from .strategies.management import StrategyManager
from .strategies.nlp import NERStrategy, SentimentStrategy, TokenizationStrategy
from .strategies.topic import TopicStrategy
from .validation.chunk_validator import ChunkValidator

if TYPE_CHECKING:
    from .types import ServiceState


class ChunkProcessor(BaseProcessor[ProcessedChunk]):
    """Processor for text chunks with NLP capabilities.

    This processor applies various NLP strategies to text chunks,
    including tokenization, named entity recognition, sentiment analysis,
    and topic identification.

    Attributes:
        settings: Application settings
        nlp: spaCy language model
        strategy_manager: Manager for processing strategies
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the processor.

        Args:
            settings: Application settings

        Raises:
            ValueError: If required settings are missing
        """
        super().__init__(settings)
        self._nlp: Language | None = None
        self._strategy_manager = StrategyManager()
        self._validator = ChunkValidator()
        self._aggregator = ResultAggregator()

    async def initialize(self) -> None:
        """Initialize NLP components and models.

        This method loads the spaCy model and initializes all processing
        strategies.

        Raises:
            ServiceInitializationError: If initialization fails
        """
        self._transition_state(ServiceState.INITIALIZING)
        try:
            if not SPACY_AVAILABLE:
                raise ServiceInitializationError(
                    "spaCy is required for chunk processing",
                    service_name=self.__class__.__name__,
                    missing_dependencies=["spacy"],
                )

            # Load spaCy model
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except OSError as e:
                raise ServiceInitializationError(
                    "Failed to load spaCy model",
                    cause=e,
                    service_name=self.__class__.__name__,
                    missing_dependencies=["en_core_web_sm"],
                )

            # Initialize strategies
            self._initialize_strategies()
            self._transition_state(ServiceState.RUNNING)

            # Add initialization metadata
            self.add_metadata("model_name", "en_core_web_sm")
            self.add_metadata("spacy_version", spacy.__version__)
            self.add_metadata("strategy_count", len(self._strategy_manager.strategies))

        except Exception as e:
            self._transition_state(ServiceState.ERROR)
            if not isinstance(e, ServiceInitializationError):
                raise ServiceInitializationError(
                    f"Failed to initialize chunk processor: {e}",
                    cause=e,
                    service_name=self.__class__.__name__,
                )
            raise

    def _initialize_strategies(self) -> None:
        """Initialize processing strategies.

        This method sets up the NLP processing pipeline by creating
        and configuring the required strategies.

        Raises:
            ServiceInitializationError: If strategy initialization fails
        """
        if self._nlp is None:
            raise ServiceInitializationError(
                "Cannot initialize strategies: spaCy model not loaded",
                service_name=self.__class__.__name__,
            )

        try:
            # Add core NLP strategies
            self._strategy_manager.add_strategy(TokenizationStrategy(self._nlp))
            self._strategy_manager.add_strategy(NERStrategy(self._nlp))
            self._strategy_manager.add_strategy(SentimentStrategy(self._nlp))
            self._strategy_manager.add_strategy(TopicStrategy())

            # Validate strategy dependencies
            self._strategy_manager.validate_dependencies()

        except Exception as e:
            raise ServiceInitializationError(
                "Failed to initialize processing strategies",
                cause=e,
                service_name=self.__class__.__name__,
            )

    def process_chunk(self, chunk: Chunk, metadata: dict[str, Any] | None = None) -> ProcessedChunk:
        """Process a single chunk.

        This method applies all registered strategies to the chunk
        in sequence, accumulating the results.

        Args:
            chunk: Chunk to process
            metadata: Optional processing metadata

        Returns:
            Processed chunk with NLP annotations

        Raises:
            ServiceStateError: If processor is not initialized
            ValidationError: If chunk is invalid
            TypeError: If chunk is not of correct type
        """
        self._check_running()

        # Validate chunk
        validation_errors = self._validator.validate(chunk, metadata)
        if validation_errors:
            raise ValidationError(
                validation_errors,
                validation_context={"chunk_id": chunk.id, "metadata": metadata},
            )

        # Add processing metadata
        if metadata:
            self.add_metadata("chunk_metadata", metadata)
        self.add_metadata("chunk_id", chunk.id)
        self.add_metadata("content_length", len(chunk.content))

        # Process with all strategies
        self._aggregator.clear()
        for strategy in self._strategy_manager.strategies:
            try:
                result = strategy.process(chunk.content, metadata)
                self._aggregator.add_result(strategy, result)
            except Exception as e:
                self.add_metadata("failed_strategy", strategy.__class__.__name__)
                raise ValidationError(
                    [f"Strategy {strategy.__class__.__name__} failed: {e}"],
                    validation_context={
                        "chunk_id": chunk.id,
                        "strategy": strategy.__class__.__name__,
                        "metadata": metadata,
                    },
                )

        return self._aggregator.build_processed_chunk(chunk)

    def process_chunks(
        self, chunks: list[Chunk], metadata: dict[str, Any] | None = None
    ) -> list[ProcessedChunk]:
        """Process multiple chunks.

        This method processes each chunk in sequence, applying all
        registered strategies.

        Args:
            chunks: Chunks to process
            metadata: Optional processing metadata

        Returns:
            List of processed chunks

        Raises:
            ServiceStateError: If processor is not initialized
            ValidationError: If any chunk is invalid
            TypeError: If any chunk is not of correct type
        """
        self._check_running()

        # Add batch processing metadata
        if metadata:
            self.add_metadata("batch_metadata", metadata)
        self.add_metadata("batch_size", len(chunks))

        # Validate all chunks first
        validation_results = self._validator.validate_batch(chunks, metadata)
        if validation_results:
            errors = [
                f"Chunk at index {i} has errors: {', '.join(errs)}"
                for i, errs in validation_results
            ]
            raise ValidationError(
                errors,
                validation_context={"batch_size": len(chunks), "metadata": metadata},
            )

        # Process chunks
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            try:
                processed = self.process_chunk(chunk, metadata)
                processed_chunks.append(processed)
            except Exception as e:
                self.add_metadata("failed_chunk_index", i)
                self.add_metadata("failed_chunk_id", chunk.id)
                raise ValidationError(
                    [f"Failed to process chunk {chunk.id}: {e}"],
                    validation_context={
                        "chunk_id": chunk.id,
                        "batch_index": i,
                        "metadata": metadata,
                    },
                )

        return processed_chunks

    def get_processing_steps(self) -> list[ProcessingStep]:
        """Get processing steps applied by this processor.

        Returns:
            List of processing steps
        """
        steps = [
            ("tokenization", "Text tokenization"),
            ("ner", "Named entity recognition"),
            ("sentiment", "Sentiment analysis"),
            ("topic", "Topic identification"),
        ]

        return [
            ProcessingStep(
                step_name=name,
                status=DocumentStatus.PROCESSED,
                error_message=None,
                completed_at=None,
            )
            for name, _ in steps
        ]
