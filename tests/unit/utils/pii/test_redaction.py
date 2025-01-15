"""Tests for PII redaction functionality."""
import pytest

from src.utils.pii_detector import PIIDetector, PIIMatch


@pytest.fixture
def pii_detector():
    """Create a PIIDetector instance."""
    return PIIDetector(spacy_model='en_core_web_sm')

def test_basic_redaction(pii_detector):
    """Test basic PII redaction."""
    text = 'Contact john.doe@email.com or call +1-555-123-4567'
    redacted = pii_detector.redact(text)
    assert '[EMAIL]' in redacted
    assert '[PHONE]' in redacted
    assert 'john.doe@email.com' not in redacted
    assert '+1-555-123-4567' not in redacted

def test_custom_redaction_patterns(pii_detector):
    """Test redaction with custom patterns."""
    text = 'Email: test@example.com'
    custom_patterns = {'email': '<<EMAIL REMOVED>>'}
    redacted = pii_detector.redact(text, custom_redaction=custom_patterns)
    assert '<<EMAIL REMOVED>>' in redacted
    assert '[EMAIL]' not in redacted

def test_redaction_with_provided_matches(pii_detector):
    """Test redaction using pre-computed matches."""
    text = 'Phone: +1-555-123-4567'
    matches = [PIIMatch(type='phone', value='+1-555-123-4567', start=7, end=21)]
    redacted = pii_detector.redact(text, matches=matches)
    assert '[PHONE]' in redacted