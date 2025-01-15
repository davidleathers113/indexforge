"""
Source reliability metrics and quality tracking.

This module provides functionality for tracking and analyzing the reliability
and quality of document sources. It includes metrics for authority, content
quality, update frequency, and metadata completeness.

Key Features:
    - Authority scoring
    - Content quality assessment
    - Update frequency tracking
    - Metadata completeness validation
    - Quality check aggregation
    - Reliability trend analysis

Example:
    ```python
    # Initialize reliability tracker
    tracker = SourceReliability(
        source_type="word",
        source_id="doc123"
    )

    # Update content quality
    tracker.update_content_quality({
        "completeness": 0.9,
        "consistency": 0.85,
        "readability": 0.95,
        "accuracy": 0.88
    })

    # Update metadata completeness
    tracker.update_metadata_completeness(
        metadata_fields=["title", "author", "date"],
        required_fields=["title", "date"]
    )

    # Get reliability score
    score = tracker.get_reliability_score()
    print(f"Overall reliability: {score:.2%}")
    ```
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class ReliabilityMetrics:
    """
    Container for source reliability metrics.

    This class holds various metrics that contribute to the overall
    reliability assessment of a document source.

    Attributes:
        authority_score: 0-1 score indicating source authority
        content_quality_score: 0-1 score for content quality
        update_frequency: Average updates per time period
        last_update: Timestamp of last update
        total_updates: Total number of updates
        quality_checks: Results of various quality checks
        metadata_completeness: 0-1 score for metadata completeness

    Example:
        ```python
        metrics = ReliabilityMetrics(
            authority_score=0.85,
            content_quality_score=0.92,
            update_frequency=1.5,
            last_update=datetime.now(timezone.utc),
            total_updates=10,
            quality_checks={
                "completeness": 0.95,
                "consistency": 0.88
            },
            metadata_completeness=0.9
        )
        ```
    """

    authority_score: float  # 0-1 score indicating source authority
    content_quality_score: float  # 0-1 score for content quality
    update_frequency: float  # Average updates per time period
    last_update: datetime  # Timestamp of last update
    total_updates: int  # Total number of updates
    quality_checks: Dict[str, float]  # Results of various quality checks
    metadata_completeness: float  # 0-1 score for metadata completeness


class SourceReliability:
    """
    Manages source reliability metrics and calculations.

    This class handles the tracking, calculation, and persistence of
    reliability metrics for document sources. It provides methods for
    updating various aspects of reliability and computing overall scores.

    Attributes:
        source_type: Type of source being tracked
        source_id: Unique identifier for the source
        metrics_dir: Directory for storing metrics data
        metrics: Current reliability metrics

    Example:
        ```python
        # Initialize tracker
        tracker = SourceReliability(
            source_type="pdf",
            source_id="doc456",
            metrics_dir="/path/to/metrics"
        )

        # Update metrics
        tracker.update_authority_score({
            "reputation": 0.9,
            "verification": 0.85,
            "expertise": 0.92
        })

        # Get metrics summary
        summary = tracker.get_metrics_summary()
        print(f"Quality score: {summary['content_quality_score']:.2f}")
        ```
    """

    def __init__(self, source_type: str, source_id: str, metrics_dir: Optional[str] = None):
        """
        Initialize source reliability tracker.

        Args:
            source_type: Type of source (e.g., 'word', 'excel')
            source_id: Unique identifier for the source
            metrics_dir: Optional directory for storing metrics
        """
        self.source_type = source_type
        self.source_id = source_id
        self.metrics_dir = Path(metrics_dir) if metrics_dir else Path(__file__).parent / "metrics"
        self.metrics = self._load_metrics()

    def _load_metrics(self) -> ReliabilityMetrics:
        """
        Load existing metrics or initialize new ones.

        Returns:
            ReliabilityMetrics object with loaded or default values

        Note:
            If metrics file exists, loads from file
            If file doesn't exist or has errors, initializes new metrics
        """
        metrics_path = self._get_metrics_path()

        try:
            if metrics_path.exists():
                with open(metrics_path, "r") as f:
                    data = json.load(f)
                    # Convert stored timestamp to datetime
                    data["last_update"] = datetime.fromisoformat(data["last_update"])
                    return ReliabilityMetrics(**data)
            else:
                logger.info(f"No existing metrics for source {self.source_id}, initializing new")
                return self._initialize_metrics()
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")
            return self._initialize_metrics()

    def _initialize_metrics(self) -> ReliabilityMetrics:
        """
        Initialize new reliability metrics.

        Returns:
            ReliabilityMetrics object with default values
        """
        return ReliabilityMetrics(
            authority_score=0.5,  # Start with neutral authority
            content_quality_score=0.5,  # Start with neutral quality
            update_frequency=0.0,
            last_update=datetime.now(timezone.utc),
            total_updates=0,
            quality_checks={},
            metadata_completeness=0.0,
        )

    def _get_metrics_path(self) -> Path:
        """
        Get path for metrics storage.

        Returns:
            Path object for the metrics file
        """
        return self.metrics_dir / f"{self.source_type}_{self.source_id}_metrics.json"

    def _save_metrics(self) -> None:
        """
        Save current metrics to file.

        Raises:
            Exception: If there are errors saving the metrics file
        """
        try:
            metrics_path = self._get_metrics_path()
            self.metrics_dir.mkdir(parents=True, exist_ok=True)

            # Convert metrics to dictionary, handling datetime
            metrics_dict = {
                "authority_score": self.metrics.authority_score,
                "content_quality_score": self.metrics.content_quality_score,
                "update_frequency": self.metrics.update_frequency,
                "last_update": self.metrics.last_update.isoformat(),
                "total_updates": self.metrics.total_updates,
                "quality_checks": self.metrics.quality_checks,
                "metadata_completeness": self.metrics.metadata_completeness,
            }

            with open(metrics_path, "w") as f:
                json.dump(metrics_dict, f, indent=2)

            logger.info(f"Saved metrics for source {self.source_id}")
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            raise

    def update_content_quality(self, content_metrics: Union[float, Dict]) -> None:
        """Update content quality metrics.

        Args:
            content_metrics: Either a float representing overall quality score (0-1)
                           or a dictionary of detailed quality metrics
        """
        logger.debug("Updating content quality metrics for source %s", self.source_id)
        logger.debug("Input metrics: %s (type: %s)", content_metrics, type(content_metrics))

        try:
            if isinstance(content_metrics, float):
                logger.debug("Converting float score %f to metrics dictionary", content_metrics)
                content_metrics = {"overall_score": content_metrics}

            logger.debug("Current quality checks: %s", self.metrics.quality_checks)
            self.metrics.quality_checks.update(content_metrics)
            logger.debug("Updated quality checks: %s", self.metrics.quality_checks)

            # Calculate overall quality score if we have the standard metrics
            standard_metrics = {"completeness", "consistency", "readability", "accuracy"}
            if all(metric in self.metrics.quality_checks for metric in standard_metrics):
                weights = {
                    "completeness": 0.3,
                    "consistency": 0.2,
                    "readability": 0.2,
                    "accuracy": 0.3,
                }
                quality_score = sum(
                    self.metrics.quality_checks[metric] * weight
                    for metric, weight in weights.items()
                )
                logger.debug("Calculated overall quality score: %f", quality_score)
                self.metrics.content_quality_score = quality_score
            elif "overall_score" in content_metrics:
                logger.debug("Using provided overall score: %f", content_metrics["overall_score"])
                self.metrics.content_quality_score = content_metrics["overall_score"]

            self._record_update()
            logger.debug("Successfully updated content quality metrics")

        except Exception as e:
            logger.error("Failed to update content quality metrics: %s", str(e))
            raise

    def update_metadata_completeness(
        self, metadata_fields: List[str], required_fields: List[str]
    ) -> None:
        """
        Update metadata completeness score.

        Args:
            metadata_fields: List of available metadata fields
            required_fields: List of required metadata fields

        Example:
            ```python
            tracker.update_metadata_completeness(
                metadata_fields=["title", "author", "date", "keywords"],
                required_fields=["title", "date"]
            )
            ```
        """
        if not required_fields:
            self.metrics.metadata_completeness = 1.0
            return

        # Calculate completeness as ratio of available required fields
        available_required = set(metadata_fields) & set(required_fields)
        completeness = len(available_required) / len(required_fields)

        self.metrics.metadata_completeness = completeness
        self._record_update()

    def update_authority_score(self, authority_metrics: Dict[str, float]) -> None:
        """
        Update source authority score.

        Args:
            authority_metrics: Dictionary of authority metrics
                - reputation: 0-1 score for source reputation
                - verification: 0-1 score for source verification
                - expertise: 0-1 score for domain expertise
                - trust: 0-1 score for trust level

        Example:
            ```python
            tracker.update_authority_score({
                "reputation": 0.85,
                "verification": 0.90,
                "expertise": 0.88,
                "trust": 0.92
            })
            ```
        """
        weights = {"reputation": 0.3, "verification": 0.3, "expertise": 0.2, "trust": 0.2}

        authority_score = sum(
            authority_metrics.get(metric, 0) * weight for metric, weight in weights.items()
        )

        self.metrics.authority_score = authority_score
        self._record_update()

    def _record_update(self) -> None:
        """
        Record an update and recalculate update frequency.

        Note:
            This is called automatically by update methods
            Updates last_update timestamp and recalculates frequency
        """
        now = datetime.now(timezone.utc)

        # Calculate time since last update
        time_diff = now - self.metrics.last_update
        seconds_diff = time_diff.total_seconds()

        # Update metrics
        self.metrics.total_updates += 1

        # Calculate updates per second, but cap it at a reasonable value
        self.metrics.update_frequency = min(
            self.metrics.total_updates / max(seconds_diff, 1),  # Avoid division by zero
            1.0,  # Cap at 1 update per second
        )
        self.metrics.last_update = now

        logger.debug(
            "Updated source metrics - Updates: %d, Time diff: %.2f seconds, Frequency: %.2f updates/second",
            self.metrics.total_updates,
            seconds_diff,
            self.metrics.update_frequency,
        )

        self._save_metrics()

    def get_reliability_score(self) -> float:
        """
        Calculate overall reliability score.

        Returns:
            Float between 0-1 indicating overall source reliability

        Example:
            ```python
            score = tracker.get_reliability_score()
            if score >= 0.8:
                print("High reliability source")
            elif score >= 0.6:
                print("Medium reliability source")
            else:
                print("Low reliability source")
            ```
        """
        weights = {"authority": 0.3, "quality": 0.3, "metadata": 0.2, "frequency": 0.2}

        # Normalize update frequency to 0-1 scale
        # Assume daily updates (1.0) is the target frequency
        normalized_frequency = min(self.metrics.update_frequency, 1.0)

        reliability_score = (
            weights["authority"] * self.metrics.authority_score
            + weights["quality"] * self.metrics.content_quality_score
            + weights["metadata"] * self.metrics.metadata_completeness
            + weights["frequency"] * normalized_frequency
        )

        return reliability_score

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of current reliability metrics.

        Returns:
            Dictionary containing current metrics and overall reliability score

        Example:
            ```python
            summary = tracker.get_metrics_summary()
            print(f"Reliability score: {summary['reliability_score']:.2f}")
            print(f"Content quality: {summary['content_quality_score']:.2f}")
            print(f"Last updated: {summary['last_update']}")
            ```
        """
        return {
            "reliability_score": self.get_reliability_score(),
            "authority_score": self.metrics.authority_score,
            "content_quality_score": self.metrics.content_quality_score,
            "metadata_completeness": self.metrics.metadata_completeness,
            "update_frequency": self.metrics.update_frequency,
            "last_update": self.metrics.last_update.isoformat(),
            "total_updates": self.metrics.total_updates,
            "quality_checks": self.metrics.quality_checks,
        }
