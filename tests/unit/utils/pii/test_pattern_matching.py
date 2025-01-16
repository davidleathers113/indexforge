"""Tests for PII pattern matching functionality."""
import pytest

from src.utils.pii_detector import PIIDetector


@pytest.fixture
def pii_detector():
    """Create a PIIDetector instance."""
    return PIIDetector(spacy_model='en_core_web_sm')


def test_regex_pattern_matching(pii_detector):
    """Test detection of various PII patterns."""
    test_cases = [('Email: test@example.com', 'email'), ('Phone: +1-555-123-4567', 'phone'), ('SSN: 123-45-6789', 'ssn'), ('Credit Card: 4111-1111-1111-1111', 'credit_card'), ('IP: 192.168.1.1', 'ip_address'), ('Date: 01/01/2024', 'date'), ('Passport: AB123456', 'passport'), ('Bitcoin: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa', 'bitcoin_address'), ('Ethereum: 0x742d35Cc6634C0532925a3b844Bc454e4438f44e', 'ethereum_address')]
    for text, expected_type in test_cases:
        matches = pii_detector._find_regex_matches(text)
        assert matches, f'Failed to detect {expected_type}'
        assert any(m.type == expected_type for m in matches)


def test_regex_pattern_case_insensitivity(pii_detector):
    """Test that regex patterns are case insensitive."""
    text = 'EMAIL: TEST@EXAMPLE.COM'
    matches = pii_detector._find_regex_matches(text)
    assert matches
    assert matches[0].type == 'email'


def test_overlapping_matches_handling(pii_detector):
    """Test handling of overlapping PII matches."""
    text = 'Contact john.doe@email.com (john.doe@email.com)'
    matches = pii_detector.detect(text)
    email_matches = [m for m in matches if m.type == 'email']
    assert len(email_matches) == 2
    for i in range(len(matches) - 1):
        assert matches[i].end <= matches[i + 1].start