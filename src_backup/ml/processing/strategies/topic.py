"""Topic identification strategy implementation."""

from typing import Any, Optional

from src.ml.processing.types import ProcessingStrategy


class TopicStrategy(ProcessingStrategy[Optional[str]]):
    """Strategy for topic identification.

    This strategy analyzes text content to identify and classify
    the main topic or theme. It can be extended to use different
    topic modeling approaches.
    """

    def __init__(self) -> None:
        """Initialize the strategy."""
        self._topics = {
            "technology": ["computer", "software", "internet", "data"],
            "science": ["research", "study", "experiment", "theory"],
            "business": ["company", "market", "finance", "industry"],
        }

    def process(self, content: str, metadata: dict[str, Any] | None = None) -> str | None:
        """Process text content to identify the main topic.

        This is a simple keyword-based implementation that can be
        replaced with more sophisticated topic modeling approaches.

        Args:
            content: Text content to process
            metadata: Optional processing metadata

        Returns:
            Identified topic ID or None if no topic matches

        Raises:
            ValueError: If content is invalid
        """
        if not content:
            raise ValueError("Content cannot be empty")

        # Convert to lowercase for matching
        content = content.lower()

        # Count keyword matches for each topic
        topic_scores = {
            topic: sum(1 for keyword in keywords if keyword in content)
            for topic, keywords in self._topics.items()
        }

        # Find topic with highest score
        if not topic_scores:
            return None

        max_score = max(topic_scores.values())
        if max_score == 0:
            return None

        # Return the first topic with max score
        for topic, score in topic_scores.items():
            if score == max_score:
                return topic

        return None  # Fallback case

    def add_topic(self, topic_id: str, keywords: list[str]) -> None:
        """Add a new topic with associated keywords.

        Args:
            topic_id: Unique identifier for the topic
            keywords: List of keywords associated with the topic

        Raises:
            ValueError: If topic_id already exists or keywords is empty
        """
        if topic_id in self._topics:
            raise ValueError(f"Topic '{topic_id}' already exists")

        if not keywords:
            raise ValueError("Keywords list cannot be empty")

        self._topics[topic_id] = [k.lower() for k in keywords]

    def remove_topic(self, topic_id: str) -> None:
        """Remove a topic and its keywords.

        Args:
            topic_id: ID of topic to remove

        Raises:
            KeyError: If topic_id doesn't exist
        """
        if topic_id not in self._topics:
            raise KeyError(f"Topic '{topic_id}' not found")

        del self._topics[topic_id]
