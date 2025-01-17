"""Content validation strategies."""


from src.ml.processing.models.chunks import Chunk
from src.ml.processing.validation.validators.base import ValidationStrategy


class SizeValidator(ValidationStrategy):
    """Validates chunk size constraints."""

    def __init__(self, min_size: int = 50, max_size: int = 10000) -> None:
        """Initialize size validator.

        Args:
            min_size: Minimum allowed chunk size
            max_size: Maximum allowed chunk size
        """
        self.min_size = min_size
        self.max_size = max_size

    def validate(self, chunk: Chunk, metadata: dict | None = None) -> list[str]:
        """Validate chunk size.

        Args:
            chunk: Chunk to validate
            metadata: Optional validation metadata

        Returns:
            List of validation error messages
        """
        errors = []
        content_length = len(chunk.content)

        if content_length > self.max_size:
            errors.append(f"Chunk content exceeds maximum length of {self.max_size} characters")
        elif content_length < self.min_size:
            errors.append(f"Chunk content is below minimum length of {self.min_size} characters")

        return errors


class ContentQualityValidator(ValidationStrategy):
    """Validates content quality metrics."""

    def __init__(self, min_density: float = 0.3) -> None:
        """Initialize quality validator.

        Args:
            min_density: Minimum ratio of meaningful content
        """
        self.min_density = min_density

    def validate(self, chunk: Chunk, metadata: dict | None = None) -> list[str]:
        """Validate content quality.

        Args:
            chunk: Chunk to validate
            metadata: Optional validation metadata

        Returns:
            List of validation error messages
        """
        errors = []
        content = chunk.content

        # Basic content checks
        if not content or not isinstance(content, str):
            errors.append("Chunk content must be a non-empty string")
            return errors
        elif len(content.strip()) == 0:
            errors.append("Chunk content cannot be empty or whitespace only")
            return errors

        # Content density check
        words = content.split()
        if not words:
            errors.append("Content contains no words")
            return errors

        meaningful_words = [w for w in words if len(w) > 2]
        content_density = len(meaningful_words) / len(words)

        if content_density < self.min_density:
            errors.append(
                f"Content density {content_density:.2f} is below minimum {self.min_density}"
            )

        # Check for repetitive content
        if self._is_repetitive(content):
            errors.append("Content contains excessive repetition")

        return errors

    def _is_repetitive(self, content: str) -> bool:
        """Check for repetitive patterns in content.

        Args:
            content: Content to check

        Returns:
            True if content appears repetitive
        """
        # Look for repeated phrases (3+ words)
        words = content.split()
        if len(words) < 6:
            return False

        phrases = [" ".join(words[i : i + 3]) for i in range(len(words) - 2)]

        phrase_counts = {}
        for phrase in phrases:
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
            if phrase_counts[phrase] > 2:  # Allow up to 2 repetitions
                return True

        return False
