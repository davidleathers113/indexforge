"""Service state definitions.

This module defines the core service lifecycle states and related types
used across the application's service layer.
"""

from enum import Enum


class ServiceState(Enum):
    """Service lifecycle states.

    These states represent the various stages of a service's lifecycle,
    from creation to termination.
    """

    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
