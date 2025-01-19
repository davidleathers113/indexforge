"""Tests for chunk processing strategies."""

from unittest.mock import Mock

from src.ml.processing.strategies import (
    NERStrategy,
    SentimentStrategy,
    TokenizationStrategy,
    TopicStrategy,
)


def test_tokenization_strategy(mock_nlp):
    """Test tokenization strategy."""
    # Setup mock tokens
    mock_tokens = [Mock(text=t) for t in ["This", "is", "a", "test"]]
    mock_doc = Mock()
    mock_doc.__iter__ = Mock(return_value=iter(mock_tokens))
    mock_nlp.__call__.return_value = mock_doc

    strategy = TokenizationStrategy(mock_nlp)
    result = strategy.process("This is a test")

    assert result == ["This", "is", "a", "test"]
    mock_nlp.__call__.assert_called_once_with("This is a test")


def test_ner_strategy(mock_nlp):
    """Test named entity recognition strategy."""
    # Setup mock entities
    mock_ents = [
        Mock(
            text="John Smith",
            label_="PERSON",
            start_char=0,
            end_char=10,
        ),
        Mock(
            text="Google",
            label_="ORG",
            start_char=15,
            end_char=21,
        ),
    ]
    mock_doc = Mock()
    mock_doc.ents = mock_ents
    mock_nlp.__call__.return_value = mock_doc

    strategy = NERStrategy(mock_nlp)
    result = strategy.process("John Smith works at Google")

    assert len(result) == 2
    assert result[0] == {
        "text": "John Smith",
        "label": "PERSON",
        "start": 0,
        "end": 10,
    }
    assert result[1] == {
        "text": "Google",
        "label": "ORG",
        "start": 15,
        "end": 21,
    }


def test_sentiment_strategy(mock_nlp):
    """Test sentiment analysis strategy."""
    # Setup mock tokens with sentiment scores
    mock_tokens = [
        Mock(sentiment=0.5),
        Mock(sentiment=0.8),
        Mock(sentiment=0.3),
    ]
    mock_doc = Mock()
    mock_doc.__iter__ = Mock(return_value=iter(mock_tokens))
    mock_doc.__len__ = Mock(return_value=len(mock_tokens))
    mock_nlp.__call__.return_value = mock_doc

    strategy = SentimentStrategy(mock_nlp)
    result = strategy.process("Test sentiment text")

    assert result == (0.5 + 0.8 + 0.3) / 3
    mock_nlp.__call__.assert_called_once_with("Test sentiment text")


def test_sentiment_strategy_empty_text(mock_nlp):
    """Test sentiment analysis with empty text."""
    mock_doc = Mock()
    mock_doc.__iter__ = Mock(return_value=iter([]))
    mock_doc.__len__ = Mock(return_value=0)
    mock_nlp.__call__.return_value = mock_doc

    strategy = SentimentStrategy(mock_nlp)
    result = strategy.process("")

    assert result == 0.0


def test_topic_strategy():
    """Test topic identification strategy."""
    strategy = TopicStrategy()
    result = strategy.process("Test topic text")

    # Currently returns None as it's a placeholder
    assert result is None
