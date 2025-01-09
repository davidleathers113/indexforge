"""Tests for PII NER (Named Entity Recognition) functionality."""
from unittest.mock import Mock, patch
import pytest
from src.utils.pii_detector import PIIDetector

@pytest.fixture
def mock_spacy_model():
    """Create a mock spaCy model."""
    with patch('spacy.load') as mock_load:
        mock_ent = Mock()
        mock_ent.label_ = 'PERSON'
        mock_ent.text = 'John Doe'
        mock_ent.start_char = 0
        mock_ent.end_char = 8
        mock_doc = Mock()
        mock_doc.ents = [mock_ent]
        mock_nlp = Mock()
        mock_nlp.return_value = mock_doc
        mock_load.return_value = mock_nlp
        yield mock_nlp

@pytest.fixture
def pii_detector(mock_spacy_model):
    """Create a PIIDetector instance with mock spaCy model."""
    return PIIDetector(spacy_model='en_core_web_sm')

def test_ner_detection(pii_detector, mock_spacy_model):
    """Test named entity recognition."""
    text = 'John Doe works at Apple Inc in New York'
    matches = pii_detector._find_ner_matches(text)
    assert matches
    assert any((m.type == 'person' for m in matches))

def test_ner_chunking(pii_detector):
    """Test NER processing with text chunking."""
    long_text = 'John Doe ' * 10000
    chunked_detector = PIIDetector(spacy_model='en_core_web_sm', chunk_size=1000)
    matches = chunked_detector._find_ner_matches(long_text)
    assert matches

def test_combined_pii_detection(pii_detector):
    """Test combined regex and NER detection."""
    text = "John Doe's email is john.doe@email.com and phone is +1-555-123-4567"
    matches = pii_detector.detect(text)
    detected_types = {m.type for m in matches}
    assert 'person' in detected_types
    assert 'email' in detected_types
    assert 'phone' in detected_types