"""
Version history tracking for source configurations and content.

This module provides functionality for tracking and managing version history of source
configurations, content changes, and metadata updates. It supports tagging versions,
tracking changes with detailed metadata, and maintaining a complete history of
modifications.

Key Features:
    - Version tagging with metadata
    - Change tracking with diff support
    - Author attribution
    - Reliability scoring
    - History persistence
    - Change categorization

Example:
    ```python
    # Initialize version history
    history = VersionHistory(
        source_type="pdf",
        source_id="doc123",
        history_dir="/path/to/storage"
    )

    # Record a change
    history.record_change(
        change_type=ChangeType.SCHEMA,
        description="Updated schema properties",
        author="john.doe",
        previous_value=old_schema,
        new_value=new_schema
    )

    # Create a version tag
    history.create_tag(
        tag="v1.0.0",
        description="Initial release",
        author="john.doe",
        change_type=ChangeType.SCHEMA
    )

    # Get history
    changes = history.get_changes(since="v1.0.0")
    ```
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import unified_diff
from enum import Enum
import json
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """
    Types of changes that can be tracked in the version history.

    Attributes:
        SCHEMA: Changes to the data schema definition
        CONFIG: Changes to configuration settings
        CONTENT: Changes to document content
        METADATA: Changes to metadata fields
        PROPERTY: Changes to individual properties
        VECTORIZER: Changes to vectorizer settings

    Example:
        ```python
        change_type = ChangeType.SCHEMA
        if change_type == ChangeType.CONFIG:
            print("Configuration change detected")
        ```
    """

    SCHEMA = "schema"
    CONFIG = "config"
    CONTENT = "content"
    METADATA = "metadata"
    PROPERTY = "property"
    VECTORIZER = "vectorizer"


@dataclass
class VersionTag:
    """
    Version tag information for marking significant points in history.

    Attributes:
        tag: Version tag string (e.g., "v1.0.0")
        timestamp: When the tag was created
        description: Description of what this version represents
        author: Who created the tag
        change_type: Type of change this version represents
        reliability_score: Optional score indicating version reliability

    Example:
        ```python
        tag = VersionTag(
            tag="v1.0.0",
            timestamp=datetime.now(timezone.utc),
            description="Initial release",
            author="john.doe",
            change_type=ChangeType.SCHEMA,
            reliability_score=0.95
        )
        ```
    """

    tag: str
    timestamp: datetime
    description: str
    author: str
    change_type: ChangeType
    reliability_score: float | None = None


@dataclass
class Change:
    """
    Represents a single change in the version history.

    Attributes:
        timestamp: When the change occurred
        change_type: Type of change (schema, config, etc.)
        description: Description of what changed
        author: Who made the change
        previous_value: Value before the change
        new_value: Value after the change
        version_tag: Optional version tag associated with this change

    Example:
        ```python
        change = Change(
            timestamp=datetime.now(timezone.utc),
            change_type=ChangeType.CONFIG,
            description="Updated vectorizer settings",
            author="jane.doe",
            previous_value={"model": "v1"},
            new_value={"model": "v2"},
            version_tag="v1.1.0"
        )
        ```
    """

    timestamp: datetime
    change_type: ChangeType
    description: str
    author: str
    previous_value: Any
    new_value: Any
    version_tag: str | None = None


class VersionHistory:
    """
    Manages version history for source configurations and content.

    This class provides functionality for tracking changes, managing version tags,
    and maintaining a complete history of modifications. It supports persistence
    of history data and provides methods for querying and analyzing changes.

    Attributes:
        source_type (str): Type of source being tracked
        source_id (str): Unique identifier for the source
        history_dir (Path): Directory for storing history data
        max_changes (int): Maximum number of changes to keep in history
        changes (List[Change]): List of recorded changes
        tags (Dict[str, VersionTag]): Dictionary of version tags

    Example:
        ```python
        # Initialize history tracker
        history = VersionHistory(
            source_type="pdf",
            source_id="doc123",
            history_dir="/data/history",
            max_changes=1000
        )

        # Record configuration change
        history.record_change(
            change_type=ChangeType.CONFIG,
            description="Updated extraction settings",
            author="john.doe",
            previous_value=old_config,
            new_value=new_config
        )

        # Create version tag
        history.create_tag(
            tag="v1.1.0",
            description="Improved extraction",
            author="john.doe",
            change_type=ChangeType.CONFIG
        )

        # Get recent changes
        recent = history.get_changes(since="v1.0.0")
        ```
    """

    def __init__(
        self,
        source_type: str,
        source_id: str,
        history_dir: str | None = None,
        max_changes: int = 1000,
    ):
        """
        Initialize version history tracker.

        Args:
            source_type: Type of source being tracked (e.g., 'pdf', 'word')
            source_id: Unique identifier for the source
            history_dir: Optional directory for storing history data
            max_changes: Maximum number of changes to keep in history

        Example:
            ```python
            # Use default storage location
            history = VersionHistory("pdf", "doc123")

            # Use custom storage location
            history = VersionHistory(
                source_type="word",
                source_id="doc456",
                history_dir="/data/history",
                max_changes=500
            )
            ```
        """
        self.source_type = source_type
        self.source_id = source_id
        self.history_dir = Path(history_dir) if history_dir else Path(__file__).parent / "history"
        self.max_changes = max_changes
        self.changes: list[Change] = []
        self.tags: dict[str, VersionTag] = {}
        self._load_history()

    def _get_history_path(self) -> Path:
        """
        Get path for history storage.

        Returns:
            Path object pointing to the history JSON file.

        Note:
            This is an internal method used to maintain consistent file paths.
        """
        return self.history_dir / f"{self.source_type}_{self.source_id}_history.json"

    def _get_tags_path(self) -> Path:
        """
        Get path for tags storage.

        Returns:
            Path object pointing to the tags JSON file.

        Note:
            This is an internal method used to maintain consistent file paths.
        """
        return self.history_dir / f"{self.source_type}_{self.source_id}_tags.json"

    def _load_history(self) -> None:
        """
        Load version history from storage.

        This method reads the history file and deserializes the data into
        Change and VersionTag objects. It handles datetime parsing and
        enum conversion automatically.

        Raises:
            Exception: If there are errors reading or parsing the history file.
                     These are caught and logged, with empty lists used as fallback.

        Note:
            This is called automatically during initialization and should not
            typically need to be called directly.
        """
        try:
            history_path = self._get_history_path()
            tags_path = self._get_tags_path()

            if history_path.exists():
                with open(history_path) as f:
                    data = json.load(f)
                self.changes = [
                    Change(
                        timestamp=datetime.fromisoformat(c["timestamp"]),
                        change_type=ChangeType(c["change_type"]),
                        description=c["description"],
                        author=c["author"],
                        previous_value=c["previous_value"],
                        new_value=c["new_value"],
                        version_tag=c.get("version_tag"),
                    )
                    for c in data
                ]

            if tags_path.exists():
                with open(tags_path) as f:
                    data = json.load(f)
                self.tags = {
                    tag: VersionTag(
                        tag=tag,
                        timestamp=datetime.fromisoformat(t["timestamp"]),
                        description=t["description"],
                        author=t["author"],
                        change_type=ChangeType(t["change_type"]),
                        reliability_score=t.get("reliability_score"),
                    )
                    for tag, t in data.items()
                }

        except Exception as e:
            logger.error(f"Error loading version history: {e}")
            self.changes = []
            self.tags = {}

    def _save_history(self) -> None:
        """
        Save current version history to storage.

        This method serializes all changes and tags to JSON format and writes
        them to their respective storage files. It handles datetime serialization
        and ensures the storage directory exists.

        Raises:
            Exception: If there are errors creating the directory or writing the files.
                     These are logged and re-raised to allow error handling by callers.
        """
        try:
            self.history_dir.mkdir(parents=True, exist_ok=True)

            # Save changes
            history_data = [
                {
                    "timestamp": c.timestamp.isoformat(),
                    "change_type": c.change_type.value,
                    "description": c.description,
                    "author": c.author,
                    "previous_value": c.previous_value,
                    "new_value": c.new_value,
                    "version_tag": c.version_tag,
                }
                for c in self.changes
            ]

            with open(self._get_history_path(), "w") as f:
                json.dump(history_data, f, indent=2)

            # Save tags
            tags_data = {
                tag: {
                    "tag": t.tag,
                    "timestamp": t.timestamp.isoformat(),
                    "description": t.description,
                    "author": t.author,
                    "change_type": t.change_type.value,
                    "reliability_score": t.reliability_score,
                }
                for tag, t in self.tags.items()
            }

            with open(self._get_tags_path(), "w") as f:
                json.dump(tags_data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving version history: {e}")
            raise

    def record_change(
        self,
        change_type: ChangeType | str,
        description: str,
        author: str,
        previous_value: Any,
        new_value: Any,
        reliability_score: float | None = None,
    ) -> None:
        """
        Record a change in the version history.

        Args:
            change_type: Type of change being recorded
            description: Description of the change
            author: Author of the change
            previous_value: Previous state/value
            new_value: New state/value
            reliability_score: Optional reliability score at time of change

        Example:
            ```python
            history.record_change(
                change_type=ChangeType.CONFIG,
                description="Updated vectorizer settings",
                author="john.doe",
                previous_value={"model": "v1"},
                new_value={"model": "v2"},
                reliability_score=0.95
            )
            ```
        """
        if isinstance(change_type, str):
            change_type = ChangeType(change_type)

        change = Change(
            timestamp=datetime.now(UTC),
            change_type=change_type,
            description=description,
            author=author,
            previous_value=previous_value,
            new_value=new_value,
        )

        self.changes.append(change)

        # Trim history if needed
        if len(self.changes) > self.max_changes:
            self.changes = self.changes[-self.max_changes :]

        self._save_history()

    def create_tag(
        self,
        tag: str,
        description: str,
        author: str,
        change_type: ChangeType | str,
        reliability_score: float | None = None,
    ) -> None:
        """
        Create a version tag.

        Args:
            tag: Tag identifier (e.g., 'v1.0.0')
            description: Description of the tagged version
            author: Author creating the tag
            change_type: Type of change being tagged
            reliability_score: Optional reliability score at time of tagging

        Raises:
            ValueError: If the tag already exists

        Example:
            ```python
            history.create_tag(
                tag="v1.0.0",
                description="Initial release",
                author="john.doe",
                change_type=ChangeType.SCHEMA,
                reliability_score=0.95
            )
            ```
        """
        if isinstance(change_type, str):
            change_type = ChangeType(change_type)

        if tag in self.tags:
            raise ValueError(f"Tag '{tag}' already exists")

        version_tag = VersionTag(
            tag=tag,
            timestamp=datetime.now(UTC),
            description=description,
            author=author,
            change_type=change_type,
            reliability_score=reliability_score,
        )

        self.tags[tag] = version_tag

        # Update the most recent change with this tag
        if self.changes:
            self.changes[-1].version_tag = tag

        self._save_history()

    def get_changes(
        self,
        change_type: ChangeType | str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        tagged_only: bool = False,
    ) -> list[Change]:
        """
        Get changes matching specified criteria.

        Args:
            change_type: Optional type of changes to retrieve
            start_time: Optional start time for changes
            end_time: Optional end time for changes
            tagged_only: Whether to return only tagged changes

        Returns:
            List of changes matching the criteria

        Example:
            ```python
            # Get all schema changes
            schema_changes = history.get_changes(change_type=ChangeType.SCHEMA)

            # Get recent tagged changes
            from datetime import datetime, timedelta
            start_time = datetime.now() - timedelta(days=7)
            recent = history.get_changes(
                start_time=start_time,
                tagged_only=True
            )
            ```
        """
        if isinstance(change_type, str):
            change_type = ChangeType(change_type)

        filtered_changes = self.changes

        if change_type:
            filtered_changes = [c for c in filtered_changes if c.change_type == change_type]

        if start_time:
            filtered_changes = [c for c in filtered_changes if c.timestamp >= start_time]

        if end_time:
            filtered_changes = [c for c in filtered_changes if c.timestamp <= end_time]

        if tagged_only:
            filtered_changes = [c for c in filtered_changes if c.version_tag]

        return filtered_changes

    def get_diff(self, previous_value: Any, new_value: Any, context_lines: int = 3) -> list[str]:
        """
        Generate a diff between two values.

        Args:
            previous_value: Previous state/value
            new_value: New state/value
            context_lines: Number of context lines in the diff

        Returns:
            List of diff lines in unified diff format

        Example:
            ```python
            # Generate diff for a configuration change
            old_config = {"model": "v1", "batch_size": 32}
            new_config = {"model": "v2", "batch_size": 64}
            diff = history.get_diff(old_config, new_config)
            print("\\n".join(diff))
            ```
        """
        if isinstance(previous_value, dict) and isinstance(new_value, dict):
            # Convert dicts to JSON strings for diffing
            previous_str = json.dumps(previous_value, indent=2).splitlines(keepends=True)
            new_str = json.dumps(new_value, indent=2).splitlines(keepends=True)
        else:
            # Convert to string and split into lines
            previous_str = str(previous_value).splitlines(keepends=True)
            new_str = str(new_value).splitlines(keepends=True)

        return list(
            unified_diff(
                previous_str,
                new_str,
                fromfile="previous",
                tofile="new",
                n=context_lines,
            )
        )

    def get_version_at_tag(self, tag: str) -> Change | None:
        """
        Get the change associated with a specific tag.

        Args:
            tag: Version tag to look up

        Returns:
            Change object if tag exists, None otherwise

        Example:
            ```python
            # Get change for a specific version
            change = history.get_version_at_tag("v1.0.0")
            if change:
                print(f"Version {change.version_tag}: {change.description}")
            ```
        """
        if tag not in self.tags:
            return None

        return next((c for c in reversed(self.changes) if c.version_tag == tag), None)

    def get_tags_between(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[VersionTag]:
        """
        Get version tags within a time range.

        Args:
            start_time: Optional start time
            end_time: Optional end time

        Returns:
            List of version tags in the specified range

        Example:
            ```python
            # Get tags from the last month
            from datetime import datetime, timedelta
            start_time = datetime.now() - timedelta(days=30)
            recent_tags = history.get_tags_between(start_time=start_time)
            for tag in recent_tags:
                print(f"{tag.tag}: {tag.description}")
            ```
        """
        filtered_tags = list(self.tags.values())

        if start_time:
            filtered_tags = [t for t in filtered_tags if t.timestamp >= start_time]

        if end_time:
            filtered_tags = [t for t in filtered_tags if t.timestamp <= end_time]

        return sorted(filtered_tags, key=lambda t: t.timestamp)
