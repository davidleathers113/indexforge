"""Alert instance validation.

This module provides validation logic for alert instances.
"""

from datetime import datetime


class AlertValidator:
    """Validator for alert instances."""

    @staticmethod
    def validate_message(message: str) -> None:
        """Validate alert message.

        Args:
            message: Alert message to validate

        Raises:
            ValueError: If message is empty or invalid
        """
        if not message.strip():
            raise ValueError("Alert message cannot be empty")

    @staticmethod
    def validate_resolution(
        resolved: bool,
        resolution_time: datetime | None,
        creation_time: datetime,
    ) -> None:
        """Validate alert resolution state.

        Args:
            resolved: Whether alert is resolved
            resolution_time: When alert was resolved
            creation_time: When alert was created

        Raises:
            ValueError: If resolution state is invalid
        """
        if resolved and not resolution_time:
            raise ValueError("Resolution time must be set for resolved alerts")
        if resolution_time and resolution_time < creation_time:
            raise ValueError("Resolution time cannot be before alert creation time")
