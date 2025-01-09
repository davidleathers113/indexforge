"""PII detection fixtures."""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from unittest.mock import MagicMock

import pytest

from ..core.base import BaseState

logger = logging.getLogger(__name__)


@dataclass
class PIIState(BaseState):
    """PII detector state."""

    findings: List[Dict] = field(default_factory=list)
    error_mode: bool = False

    def reset(self):
        """Reset state to defaults."""
        super().reset()
        self.findings.clear()
        self.error_mode = False

    def add_finding(self, finding_type: str, value: str, confidence: float):
        """Add a PII finding."""
        self.findings.append({"type": finding_type, "value": value, "confidence": confidence})


@pytest.fixture(scope="function")
def pii_state():
    """Shared PII detector state."""
    state = PIIState()
    yield state
    state.reset()


@pytest.fixture(scope="function")
def mock_pii_detector(pii_state):
    """Mock PII detector for testing."""
    mock_detector = MagicMock()

    def mock_detect(text: str) -> List[Dict]:
        """Detect PII in text."""
        try:
            if pii_state.error_mode:
                pii_state.add_error("PII detection failed in error mode")
                raise ValueError("PII detection failed in error mode")

            pii_findings = []
            if "@" in text:
                pii_state.add_finding("email", "[REDACTED_EMAIL]", 0.95)
                pii_findings.append(pii_state.findings[-1])
            if any(c.isdigit() for c in text):
                digits = sum(1 for c in text if c.isdigit())
                if digits >= 10:
                    pii_state.add_finding("phone", "[REDACTED_PHONE]", 0.90)
                    pii_findings.append(pii_state.findings[-1])
            return pii_findings

        except Exception as e:
            pii_state.add_error(str(e))
            raise

    def mock_redact(text: str) -> str:
        """Redact PII from text."""
        try:
            findings = mock_detect(text)
            redacted = text
            for finding in findings:
                if finding["type"] == "email":
                    words = redacted.split()
                    redacted = " ".join(finding["value"] if "@" in word else word for word in words)
                elif finding["type"] == "phone":
                    words = redacted.split()
                    redacted = " ".join(
                        finding["value"] if any(c.isdigit() for c in word) else word
                        for word in words
                    )
            return redacted

        except Exception as e:
            pii_state.add_error(str(e))
            raise

    def analyze_document(doc: Dict) -> Dict:
        """Analyze document for PII."""
        try:
            if pii_state.error_mode:
                pii_state.add_error("Document PII analysis failed in error mode")
                raise ValueError("Document PII analysis failed in error mode")

            # Get text content
            text = doc.get("content", {}).get("body", "")
            
            # Detect and redact PII
            findings = mock_detect(text)
            redacted = mock_redact(text)
            
            # Update document
            doc.setdefault("content", {})["body"] = redacted
            doc.setdefault("metadata", {})["pii_findings"] = findings
            doc["processed"] = True
            
            return doc

        except Exception as e:
            pii_state.add_error(str(e))
            raise

    # Configure mock methods
    mock_detector.detect = MagicMock(side_effect=mock_detect)
    mock_detector.redact = MagicMock(side_effect=mock_redact)
    mock_detector.analyze_document = MagicMock(side_effect=analyze_document)
    mock_detector.get_errors = pii_state.get_errors
    mock_detector.reset = pii_state.reset
    mock_detector.set_error_mode = lambda enabled=True: setattr(pii_state, "error_mode", enabled)

    yield mock_detector
    pii_state.reset()
