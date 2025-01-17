"""Personally Identifiable Information (PII) detection and redaction.

This module provides comprehensive PII detection and redaction capabilities using
both regex patterns and Named Entity Recognition (NER). It includes:

1. PII Detection:
   - Email addresses
   - Phone numbers (international support)
   - Social Security Numbers
   - Credit card numbers
   - IP addresses
   - Dates
   - Passport numbers
   - Cryptocurrency addresses
   - Named entities (people, organizations, locations)

2. Text Processing:
   - Chunked processing for large texts
   - Clean text handling
   - Special character handling
   - Multi-language support

3. Redaction:
   - Customizable redaction patterns
   - Context preservation
   - Position-aware replacement
   - Overlap handling

4. Document Analysis:
   - Metadata generation
   - PII statistics
   - Type categorization
   - Timestamp tracking

Usage:
    ```python
    from src.utils.pii_detector import PIIDetector

    detector = PIIDetector()

    # Simple detection
    matches = detector.detect("Email me at john@example.com")
    print(matches)  # [PIIMatch(type="email", value="john@example.com", ...)]

    # Redaction
    redacted = detector.redact("Call me at 123-456-7890")
    print(redacted)  # "Call me at [PHONE]"

    # Document analysis
    doc = {
        "content": {"body": "Contact: john@example.com"},
        "metadata": {}
    }
    processed_doc = detector.analyze_document(doc)
    ```

Note:
    - Uses spaCy for NER (requires model download)
    - Handles large documents efficiently through chunking
    - Thread-safe operations
    - Customizable redaction patterns
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime

import spacy

from .text_processing import chunk_text_by_chars, clean_text


@dataclass
class PIIMatch:
    """A detected PII instance.

    Attributes:
        type: Type of PII (email, phone, person, etc.)
        value: The actual PII value found
        start: Starting position in the text
        end: Ending position in the text
    """

    type: str
    value: str
    start: int
    end: int


class PIIDetector:
    """Detector for personally identifiable information (PII) in text.

    This class provides functionality to detect and redact various types of PII
    including names, email addresses, phone numbers, and other sensitive information.
    It uses a combination of regex patterns and NER models for detection.

    Attributes:
        spacy_model: Name of the spaCy model to use for NER
        chunk_size: Size of text chunks for processing (in characters)
        logger: Logger instance for tracking operations
    """

    def __init__(self, spacy_model: str = "en_core_web_sm", chunk_size: int = 100000):
        """Initialize the PII detector.

        Args:
            spacy_model: Name of the spaCy model to use for NER detection
            chunk_size: Maximum size of text chunks for processing (in characters)
        """
        # Load spaCy model for NER
        self.nlp = spacy.load(spacy_model)
        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)

        # Common regex patterns
        self.patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            # International phone support
            "phone": (r"\+?(?:\d{1,4}[-.\s]?)?\(?\d{1,4}\)?" r"[-.\s]?\d{1,4}[-.\s]?\d{1,4}"),
            "ssn": r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b",  # Handles both hyphen and dot separators
            "credit_card": (r"\b(?:\d[ -]*?){13,16}\b|" r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
            "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            "date": (
                r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|"
                r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
                r"[a-z]* \d{1,2},? \d{4}\b"
            ),
            "passport": r"\b[A-Z]{1,2}[0-9]{6,9}\b",
            "bitcoin_address": r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b",
            "ethereum_address": r"\b0x[a-fA-F0-9]{40}\b",
        }

        # NER types to detect
        self.ner_types = {
            "PERSON": "person",
            "ORG": "organization",
            "GPE": "location",
            "LOC": "location",
            "FAC": "facility",
            "MONEY": "money",
            "PRODUCT": "product",
            "EVENT": "event",
            "LAW": "law",
            "NORP": "group",  # nationalities, religious or political groups
        }

        # Compile regex patterns
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE) for name, pattern in self.patterns.items()
        }

    def _find_regex_matches(self, text: str) -> list[PIIMatch]:
        """Find PII using regex patterns."""
        matches = []

        for pii_type, pattern in self.compiled_patterns.items():
            try:
                for match in pattern.finditer(text):
                    matches.append(
                        PIIMatch(
                            type=pii_type, value=match.group(), start=match.start(), end=match.end()
                        )
                    )
            except Exception as e:
                self.logger.error(f"Error matching pattern {pii_type}: {e!s}")

        return matches

    def _find_ner_matches(self, text: str) -> list[PIIMatch]:
        """Find PII using named entity recognition with chunking."""
        matches = []
        chunks = chunk_text_by_chars(text, chunk_size=self.chunk_size)
        offset = 0

        for chunk in chunks:
            try:
                # Clean text before NER processing
                cleaned_chunk = clean_text(chunk)
                doc = self.nlp(cleaned_chunk)

                for ent in doc.ents:
                    if ent.label_ in self.ner_types:
                        matches.append(
                            PIIMatch(
                                type=self.ner_types[ent.label_],
                                value=ent.text,
                                start=ent.start_char + offset,
                                end=ent.end_char + offset,
                            )
                        )
            except Exception as e:
                self.logger.error(f"Error processing NER chunk: {e!s}")

            offset += len(chunk)

        return matches

    def detect(self, text: str) -> list[PIIMatch]:
        """Detect all PII in the given text."""
        if not text:
            return []

        # Clean text before processing
        text = clean_text(text)

        # Combine regex and NER matches
        matches = self._find_regex_matches(text) + self._find_ner_matches(text)

        # Sort by start position and remove duplicates
        matches.sort(key=lambda x: (x.start, x.end))
        unique_matches = []
        last_end = -1

        for match in matches:
            # Skip overlapping matches
            if match.start >= last_end:
                unique_matches.append(match)
                last_end = match.end

        return unique_matches

    def redact(
        self, text: str, matches: list[PIIMatch] = None, custom_redaction: dict[str, str] = None
    ) -> str:
        """Redact PII from text with custom redaction patterns."""
        if not text:
            return text

        if matches is None:
            matches = self.detect(text)

        # Default redaction patterns
        redaction_patterns = {
            "email": "[EMAIL]",
            "phone": "[PHONE]",
            "person": "[PERSON]",
            "organization": "[ORG]",
            "location": "[LOCATION]",
            "money": "[MONEY]",
            "date": "[DATE]",
            "ssn": "[SSN]",
            "credit_card": "[CREDIT_CARD]",
            "ip_address": "[IP]",
            "passport": "[PASSPORT]",
            "bitcoin_address": "[BITCOIN]",
            "ethereum_address": "[ETH]",
        }

        # Update with custom patterns if provided
        if custom_redaction:
            redaction_patterns.update(custom_redaction)

        # Sort matches in reverse order to avoid offset issues
        matches.sort(key=lambda x: x.start, reverse=True)

        # Create a mutable list of characters
        chars = list(text)

        for match in matches:
            redaction = redaction_patterns.get(match.type, f"[REDACTED:{match.type}]")
            chars[match.start : match.end] = list(redaction)

        return "".join(chars)

    def analyze_document(self, doc: dict, custom_redaction: dict[str, str] = None) -> dict:
        """Analyze a document for PII and add results to metadata."""
        content = doc["content"]["body"]
        matches = self.detect(content)

        # Add PII analysis to metadata
        doc["metadata"]["pii_analysis"] = {
            "timestamp": datetime.utcnow().isoformat(),
            "found_types": list({match.type for match in matches}),
            "match_count": len(matches),
            "matches_by_type": {
                pii_type: len([m for m in matches if m.type == pii_type])
                for pii_type in set(match.type for match in matches)
            },
        }

        # Optionally redact content if specified
        if doc.get("redact_pii"):
            doc["content"]["body"] = self.redact(content, matches, custom_redaction)
            if doc["content"].get("summary"):
                doc["content"]["summary"] = self.redact(
                    doc["content"]["summary"],
                    self.detect(doc["content"]["summary"]),
                    custom_redaction,
                )

        return doc
