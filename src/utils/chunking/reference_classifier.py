"""Reference type classification for chunk relationships.

This module provides functionality for classifying references between chunks
into direct, indirect, and structural types, with rich metadata for each type.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Tuple
from uuid import UUID

from .citation_detector import CitationType
from .references import ReferenceManager, ReferenceType


class ReferenceCategory(Enum):
    """High-level categories for references."""

    DIRECT = auto()  # Explicit references (quotes, citations)
    INDIRECT = auto()  # Implicit references (similar content, related topics)
    STRUCTURAL = auto()  # Document structure (TOC, sections)


@dataclass
class ReferenceClassification:
    """Classification details for a reference."""

    category: ReferenceCategory
    confidence: float  # Classification confidence score (0-1)
    evidence: Dict  # Supporting evidence for classification
    metadata: Dict  # Additional metadata about the reference


class ReferenceClassifier:
    """Classifies references between chunks into semantic categories."""

    def __init__(self, ref_manager: ReferenceManager):
        """Initialize the reference classifier.

        Args:
            ref_manager: Reference manager containing references to classify
        """
        self.ref_manager = ref_manager
        self._initialize_classification_rules()

    def _initialize_classification_rules(self):
        """Initialize rules for reference classification."""
        # Map reference types to categories
        self.type_categories = {
            # Direct references
            ReferenceType.CITATION: ReferenceCategory.DIRECT,
            ReferenceType.LINK: ReferenceCategory.DIRECT,
            ReferenceType.CONTINUATION: ReferenceCategory.DIRECT,
            # Indirect references
            ReferenceType.RELATED: ReferenceCategory.INDIRECT,
            ReferenceType.SIMILAR: ReferenceCategory.INDIRECT,
            ReferenceType.CONTEXT: ReferenceCategory.INDIRECT,
            # Structural references
            ReferenceType.PARENT: ReferenceCategory.STRUCTURAL,
            ReferenceType.CHILD: ReferenceCategory.STRUCTURAL,
            ReferenceType.NEXT: ReferenceCategory.STRUCTURAL,
            ReferenceType.PREVIOUS: ReferenceCategory.STRUCTURAL,
            ReferenceType.TOC: ReferenceCategory.STRUCTURAL,
        }

    def classify_reference(
        self, source_id: UUID, target_id: UUID, ref_type: ReferenceType
    ) -> ReferenceClassification:
        """Classify a reference between two chunks.

        Args:
            source_id: ID of the source chunk
            target_id: ID of the target chunk
            ref_type: Type of reference to classify

        Returns:
            Classification details for the reference

        Raises:
            ValueError: If reference doesn't exist
        """
        # Verify reference exists
        if (source_id, target_id) not in self.ref_manager._references:
            raise ValueError(f"No reference exists between {source_id} and {target_id}")

        ref = self.ref_manager._references[(source_id, target_id)]
        category = self.type_categories[ref_type]

        # Gather evidence based on reference type and metadata
        evidence = self._gather_classification_evidence(ref)
        confidence = self._calculate_confidence(evidence)

        # Enrich metadata based on classification
        metadata = self._enrich_metadata(ref, category, evidence)

        return ReferenceClassification(
            category=category,
            confidence=confidence,
            evidence=evidence,
            metadata=metadata,
        )

    def _gather_classification_evidence(self, ref) -> Dict:
        """Gather evidence to support reference classification."""
        evidence = {
            "ref_type": ref.ref_type.value,
            "metadata": ref.metadata.copy() if ref.metadata else {},
            "bidirectional": ref.bidirectional,
        }

        # Add citation-specific evidence
        if ref.ref_type == ReferenceType.CITATION and "citation_type" in ref.metadata:
            citation_type = ref.metadata["citation_type"]
            evidence["citation_details"] = {
                "type": citation_type,
                "is_direct_quote": citation_type == CitationType.DIRECT_QUOTE.value,
                "is_inline_ref": citation_type == CitationType.INLINE_REFERENCE.value,
            }

        # Add structural evidence
        if ref.ref_type in {ReferenceType.PARENT, ReferenceType.CHILD}:
            evidence["structural_details"] = {
                "is_hierarchical": True,
                "direction": "parent" if ref.ref_type == ReferenceType.PARENT else "child",
            }

        # Add semantic evidence
        if "similarity_score" in ref.metadata:
            evidence["semantic_details"] = {
                "similarity_score": ref.metadata["similarity_score"],
                "is_highly_similar": ref.metadata["similarity_score"] >= 0.8,
            }

        return evidence

    def _calculate_confidence(self, evidence: Dict) -> float:
        """Calculate confidence score for classification."""
        confidence = 0.5  # Base confidence

        # Adjust based on evidence types
        if "citation_details" in evidence:
            confidence += 0.3  # High confidence for citations
            if evidence["citation_details"].get("is_direct_quote"):
                confidence += 0.1  # Even higher for direct quotes

        if "structural_details" in evidence:
            confidence += 0.25  # Good confidence for structural refs

        if "semantic_details" in evidence:
            sim_score = evidence["semantic_details"]["similarity_score"]
            confidence += min(0.2, sim_score * 0.25)  # Proportional to similarity

        return min(1.0, confidence)  # Cap at 1.0

    def _enrich_metadata(self, ref, category: ReferenceCategory, evidence: Dict) -> Dict:
        """Enrich reference metadata with classification details."""
        metadata = ref.metadata.copy() if ref.metadata else {}

        # Add classification metadata
        metadata["reference_category"] = category.name
        metadata["classification_evidence"] = evidence

        # Add category-specific metadata
        if category == ReferenceCategory.DIRECT:
            metadata["is_explicit_reference"] = True
            if "citation_details" in evidence:
                metadata["citation_info"] = evidence["citation_details"]

        elif category == ReferenceCategory.INDIRECT:
            metadata["is_semantic_reference"] = True
            if "semantic_details" in evidence:
                metadata["semantic_info"] = evidence["semantic_details"]

        elif category == ReferenceCategory.STRUCTURAL:
            metadata["is_structural_reference"] = True
            if "structural_details" in evidence:
                metadata["structural_info"] = evidence["structural_details"]

        return metadata

    def classify_all_references(self) -> Dict[Tuple[UUID, UUID], ReferenceClassification]:
        """Classify all references in the reference manager.

        Returns:
            Dictionary mapping (source_id, target_id) to their classifications
        """
        classifications = {}
        for (source_id, target_id), ref in self.ref_manager._references.items():
            try:
                classification = self.classify_reference(source_id, target_id, ref.ref_type)
                classifications[(source_id, target_id)] = classification
            except ValueError:
                continue  # Skip invalid references

        return classifications

    def update_reference_metadata(self, source_id: UUID, target_id: UUID) -> None:
        """Update reference metadata with classification information.

        Args:
            source_id: ID of the source chunk
            target_id: ID of the target chunk

        Raises:
            ValueError: If reference doesn't exist
        """
        if (source_id, target_id) not in self.ref_manager._references:
            raise ValueError(f"No reference exists between {source_id} and {target_id}")

        ref = self.ref_manager._references[(source_id, target_id)]
        classification = self.classify_reference(source_id, target_id, ref.ref_type)

        # Update reference metadata
        ref.metadata.update(classification.metadata)

        # Update reverse reference if bidirectional
        if ref.bidirectional and (target_id, source_id) in self.ref_manager._references:
            reverse_ref = self.ref_manager._references[(target_id, source_id)]
            reverse_ref.metadata.update(classification.metadata)
