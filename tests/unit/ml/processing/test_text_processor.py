"""Unit tests for the text processor implementation."""

from unittest.mock import patch

import pytest

from src.core.settings import Settings
from src.ml.processing.errors import ServiceInitializationError
from src.ml.processing.text import TextProcessor
from src.ml.processing.types import ServiceState


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings()


@pytest.fixture
def text_processor(settings):
    """Create a text processor instance."""
    return TextProcessor(settings)


class TestTextProcessor:
    """Test suite for TextProcessor class."""

    def test_init_without_nltk(self, settings):
        """Test initialization fails when NLTK is not available."""
        with patch("src.ml.processing.text.NLTK_AVAILABLE", False):
            with pytest.raises(ImportError) as exc_info:
                TextProcessor(settings)
            assert "NLTK is required" in str(exc_info.value)

    def test_init_with_invalid_settings(self):
        """Test initialization fails with invalid settings."""
        with pytest.raises(ValueError):
            TextProcessor(None)

    def test_initialize_downloads_nltk_data(self, text_processor):
        """Test initialization downloads required NLTK data."""
        with patch("nltk.data.find") as mock_find:
            mock_find.side_effect = LookupError()
            with patch("nltk.download") as mock_download:
                text_processor.initialize()
                mock_download.assert_called_once_with("punkt")
                assert text_processor._state == ServiceState.RUNNING

    def test_initialize_handles_download_error(self, text_processor):
        """Test initialization handles NLTK download errors."""
        with patch("nltk.data.find") as mock_find:
            mock_find.side_effect = Exception("Download failed")
            with pytest.raises(ServiceInitializationError) as exc_info:
                text_processor.initialize()
            assert "Failed to initialize NLTK resources" in str(exc_info.value)
            assert text_processor._state == ServiceState.ERROR

    def test_cleanup(self, text_processor):
        """Test cleanup properly stops the processor."""
        text_processor.cleanup()
        assert text_processor._state == ServiceState.STOPPED

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ("  Hello   World  ", "Hello World"),
            ("Hello, World!", "Hello, World!"),
            ("Special@#$%^&*Chars", "SpecialChars"),
            ("Multiple     Spaces", "Multiple Spaces"),
            ("Preserve.Punctuation!", "Preserve.Punctuation!"),
        ],
    )
    def test_normalize_text(self, text_processor, input_text, expected):
        """Test text normalization with various inputs."""
        assert text_processor.normalize_text(input_text) == expected

    def test_normalize_text_empty_input(self, text_processor):
        """Test normalization fails with empty input."""
        with pytest.raises(ValueError) as exc_info:
            text_processor.normalize_text("")
        assert "Text cannot be empty" in str(exc_info.value)

    @pytest.mark.parametrize(
        "input_text,expected_count",
        [
            ("This is one sentence.", 1),
            ("This is one. This is two.", 2),
            ("Hello Dr. Smith! How are you? I'm fine.", 3),
            ("Multiple! Short? Sentences. Here.", 4),
        ],
    )
    def test_split_sentences(self, text_processor, input_text, expected_count):
        """Test sentence splitting with various inputs."""
        with patch("nltk.tokenize.sent_tokenize") as mock_tokenize:
            mock_tokenize.return_value = ["sentence"] * expected_count
            sentences = text_processor.split_sentences(input_text)
            assert len(sentences) == expected_count
            mock_tokenize.assert_called_once_with(input_text)

    def test_split_sentences_empty_input(self, text_processor):
        """Test sentence splitting fails with empty input."""
        with pytest.raises(ValueError) as exc_info:
            text_processor.split_sentences("")
        assert "Text cannot be empty" in str(exc_info.value)

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            (
                "Check out http://example.com and email@test.com",
                "check out and",
            ),
            (
                "UPPER case TEXT with HTTP://CAPS.COM",
                "upper case text with",
            ),
            (
                "Multiple www.sites.com and multiple@emails.com in text",
                "multiple and in text",
            ),
            (
                "Special chars @#$% but keep punctuation!",
                "special chars but keep punctuation!",
            ),
        ],
    )
    def test_clean_text(self, text_processor, input_text, expected):
        """Test text cleaning with various inputs."""
        assert text_processor.clean_text(input_text) == expected

    def test_clean_text_empty_input(self, text_processor):
        """Test cleaning fails with empty input."""
        with pytest.raises(ValueError) as exc_info:
            text_processor.clean_text("")
        assert "Text cannot be empty" in str(exc_info.value)

    def test_lifecycle(self, text_processor):
        """Test complete processor lifecycle."""
        # Initial state
        assert text_processor._state == ServiceState.CREATED

        # Initialize
        with patch("nltk.data.find"):
            text_processor.initialize()
            assert text_processor._state == ServiceState.RUNNING

        # Process some text
        text = "Hello, World! This is a test."
        normalized = text_processor.normalize_text(text)
        assert normalized == "Hello, World! This is a test."

        # Cleanup
        text_processor.cleanup()
        assert text_processor._state == ServiceState.STOPPED
