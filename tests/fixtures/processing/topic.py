"""Topic clustering fixtures."""

from dataclasses import dataclass, field
import logging
from unittest.mock import MagicMock

import pytest

from ..core.base import BaseState


logger = logging.getLogger(__name__)


@dataclass
class TopicState(BaseState):
    """Topic clusterer state."""

    clusters: dict[str, list[str]] = field(default_factory=dict)
    topics: dict[str, list[str]] = field(default_factory=dict)
    error_mode: bool = False
    min_word_length: int = 3
    max_topics_per_text: int = 3

    def reset(self):
        """Reset state to defaults."""
        super().reset()
        self.clusters.clear()
        self.topics.clear()
        self.error_mode = False
        self.min_word_length = 3
        self.max_topics_per_text = 3


@pytest.fixture(scope="function")
def topic_state():
    """Shared topic clustering state."""
    state = TopicState()
    yield state
    state.reset()


@pytest.fixture(scope="function")
def mock_topic_clusterer(topic_state):
    """Mock topic clusterer for testing."""
    mock_clusterer = MagicMock()

    def mock_cluster(texts: list[str]) -> dict[str, list[str]]:
        """Cluster texts into topics."""
        try:
            if topic_state.error_mode:
                topic_state.add_error("Topic clustering failed in error mode")
                raise ValueError("Topic clustering failed in error mode")

            # Simple clustering based on common words
            topic_state.clusters.clear()
            for text in texts:
                words = [w.lower() for w in text.split() if len(w) > topic_state.min_word_length]
                if not words:
                    continue
                key = max(set(words), key=words.count)
                if key not in topic_state.clusters:
                    topic_state.clusters[key] = []
                topic_state.clusters[key].append(text)
            return topic_state.clusters.copy()

        except Exception as e:
            topic_state.add_error(str(e))
            raise

    def mock_extract_topics(texts: list[str]) -> dict[str, list[str]]:
        """Extract topics from texts."""
        try:
            if topic_state.error_mode:
                topic_state.add_error("Topic extraction failed in error mode")
                raise ValueError("Topic extraction failed in error mode")

            topic_state.topics.clear()
            for text in texts:
                words = [w.lower() for w in text.split() if len(w) > topic_state.min_word_length]
                if not words:
                    continue
                unique_words = sorted(set(words), key=lambda w: (-words.count(w), w))[
                    : topic_state.max_topics_per_text
                ]
                for word in unique_words:
                    if word not in topic_state.topics:
                        topic_state.topics[word] = []
                    topic_state.topics[word].append(text)
            return topic_state.topics.copy()

        except Exception as e:
            topic_state.add_error(str(e))
            raise

    def cluster_documents(documents: list[dict], config=None) -> list[dict]:
        """Mock document clustering."""
        try:
            if topic_state.error_mode:
                topic_state.add_error("Topic clustering failed in error mode")
                raise ValueError("Topic clustering failed in error mode")

            # Extract text from documents
            texts = [doc.get("content", {}).get("body", "") for doc in documents]
            
            # Get clusters
            clusters = mock_cluster(texts)
            
            # Add cluster info to documents
            for doc, text in zip(documents, texts, strict=False):
                for cluster_id, cluster_texts in clusters.items():
                    if text in cluster_texts:
                        doc.setdefault("metadata", {})["clustering"] = {
                            "cluster_id": cluster_id,
                            "cluster_size": len(cluster_texts),
                            "keywords": [cluster_id],  # Use cluster ID as keyword
                            "similarity_to_centroid": 1.0  # Mock similarity
                        }
                        break
            
            return documents

        except Exception as e:
            topic_state.add_error(str(e))
            raise

    # Configure mock methods
    mock_clusterer.cluster = MagicMock(side_effect=mock_cluster)
    mock_clusterer.extract_topics = MagicMock(side_effect=mock_extract_topics)
    mock_clusterer.cluster_documents = MagicMock(side_effect=cluster_documents)
    mock_clusterer.get_errors = topic_state.get_errors
    mock_clusterer.reset = topic_state.reset
    mock_clusterer.set_error_mode = lambda enabled=True: setattr(topic_state, "error_mode", enabled)

    yield mock_clusterer
    topic_state.reset()
