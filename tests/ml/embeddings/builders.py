"""Test data builders for embedding tests."""

from dataclasses import dataclass, field

from src.core.models.chunks import Chunk


@dataclass
class ChunkBuilder:
    """Builder for test chunks.

    This builder provides a fluent interface for creating test chunks
    with various configurations.
    """

    content: str = "Default test content"
    metadata: dict = field(default_factory=dict)

    def with_content(self, content: str) -> "ChunkBuilder":
        """Set chunk content.

        Args:
            content: The content to use for the chunk

        Returns:
            Self for method chaining
        """
        self.content = content
        return self

    def with_metadata(self, metadata: dict) -> "ChunkBuilder":
        """Set chunk metadata.

        Args:
            metadata: The metadata to use for the chunk

        Returns:
            Self for method chaining
        """
        self.metadata = metadata
        return self

    def build(self) -> Chunk:
        """Create the chunk instance.

        Returns:
            A new Chunk instance with the configured properties
        """
        return Chunk(content=self.content, metadata=self.metadata)

    @classmethod
    def valid(cls) -> Chunk:
        """Create a valid chunk for testing.

        Returns:
            A chunk with valid test content
        """
        return cls().build()

    @classmethod
    def invalid(cls) -> Chunk:
        """Create an invalid chunk for testing.

        Returns:
            A chunk with invalid (empty) content
        """
        return cls().with_content("").build()
