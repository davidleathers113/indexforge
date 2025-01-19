"""Version history validation.

This module provides validation rules and utilities for version operations.
Ensures data integrity and consistency in version history tracking.
"""

from datetime import datetime
import logging
import re

from src.core.lineage.version.models import Change, VersionTag
from src.core.lineage.version.types import VersionError


logger = logging.getLogger(__name__)


class VersionValidationError(VersionError):
    """Error raised when version validation fails."""


class VersionValidator:
    """Validates version operations and data integrity."""

    VERSION_TAG_PATTERN = re.compile(r"^v\d+(\.\d+)*(-[a-zA-Z0-9]+)?$")
    MAX_DESCRIPTION_LENGTH = 1000
    MIN_RELIABILITY_SCORE = 0.0
    MAX_RELIABILITY_SCORE = 1.0

    @classmethod
    def validate_tag_format(cls, tag: str) -> None:
        """Validate version tag format.

        Args:
            tag: Version tag string to validate

        Raises:
            VersionValidationError: If tag format is invalid
        """
        if not cls.VERSION_TAG_PATTERN.match(tag):
            raise VersionValidationError(
                f"Invalid version tag format: {tag}. Must match pattern: vX.Y.Z[-suffix]"
            )

    @classmethod
    def validate_description(cls, description: str) -> None:
        """Validate description length and content.

        Args:
            description: Description to validate

        Raises:
            VersionValidationError: If description is invalid
        """
        if len(description) > cls.MAX_DESCRIPTION_LENGTH:
            raise VersionValidationError(
                f"Description too long: {len(description)} chars. "
                f"Maximum allowed: {cls.MAX_DESCRIPTION_LENGTH}"
            )

    @classmethod
    def validate_reliability_score(cls, score: float | None) -> None:
        """Validate reliability score range.

        Args:
            score: Score to validate, if provided

        Raises:
            VersionValidationError: If score is invalid
        """
        if (
            score is not None
            and not cls.MIN_RELIABILITY_SCORE <= score <= cls.MAX_RELIABILITY_SCORE
        ):
            raise VersionValidationError(
                f"Invalid reliability score: {score}. Must be between "
                f"{cls.MIN_RELIABILITY_SCORE} and {cls.MAX_RELIABILITY_SCORE}"
            )

    @classmethod
    def validate_change(cls, change: Change) -> None:
        """Validate a change record.

        Args:
            change: Change record to validate

        Raises:
            VersionValidationError: If change is invalid
        """
        # Validate required fields
        if not change.description:
            raise VersionValidationError("Change description is required")
        if not change.author:
            raise VersionValidationError("Change author is required")

        # Validate field contents
        cls.validate_description(change.description)
        cls.validate_reliability_score(change.reliability_score)

        # Validate timestamps
        if change.timestamp > datetime.now(change.timestamp.tzinfo):
            raise VersionValidationError("Change timestamp cannot be in the future")

        # Validate metadata
        if not isinstance(change.metadata, dict):
            raise VersionValidationError("Change metadata must be a dictionary")

    @classmethod
    def validate_version_tag(cls, version: VersionTag) -> None:
        """Validate a version tag.

        Args:
            version: Version tag to validate

        Raises:
            VersionValidationError: If version tag is invalid
        """
        # Validate tag format
        cls.validate_tag_format(version.tag)

        # Validate fields
        cls.validate_description(version.description)
        cls.validate_reliability_score(version.reliability_score)

        # Validate timestamps
        if version.timestamp > datetime.now(version.timestamp.tzinfo):
            raise VersionValidationError("Version timestamp cannot be in the future")

        # Validate changes
        for change in version.changes:
            cls.validate_change(change)

        # Validate metadata
        if not isinstance(version.metadata, dict):
            raise VersionValidationError("Version metadata must be a dictionary")

    @classmethod
    def validate_version_sequence(cls, versions: list[VersionTag]) -> None:
        """Validate a sequence of version tags.

        Args:
            versions: List of version tags to validate

        Raises:
            VersionValidationError: If version sequence is invalid
        """
        if not versions:
            return

        # Check timestamp ordering
        for i in range(1, len(versions)):
            if versions[i].timestamp < versions[i - 1].timestamp:
                raise VersionValidationError(
                    f"Version {versions[i].tag} has earlier timestamp than {versions[i - 1].tag}"
                )

        # Validate each version
        for version in versions:
            cls.validate_version_tag(version)

    @classmethod
    def validate_change_history(cls, changes: list[Change]) -> None:
        """Validate a change history sequence.

        Args:
            changes: List of changes to validate

        Raises:
            VersionValidationError: If change history is invalid
        """
        if not changes:
            return

        # Track parent-child relationships
        change_ids = {str(change.id) for change in changes}
        for change in changes:
            if change.parent_id and str(change.parent_id) not in change_ids:
                raise VersionValidationError(
                    f"Change {change.id} references non-existent parent {change.parent_id}"
                )

        # Check timestamp ordering
        for i in range(1, len(changes)):
            if changes[i].timestamp < changes[i - 1].timestamp:
                raise VersionValidationError(
                    f"Change {changes[i].id} has earlier timestamp than {changes[i - 1].id}"
                )

        # Validate each change
        for change in changes:
            cls.validate_change(change)
