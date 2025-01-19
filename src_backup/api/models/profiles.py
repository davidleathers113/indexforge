"""User profile models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User role enumeration."""

    USER = "user"
    ADMIN = "admin"


class ProfileBase(BaseModel):
    """Base profile model."""

    name: str | None = None
    avatar_url: str | None = None
    role: UserRole = Field(default=UserRole.USER)


class ProfileCreate(ProfileBase):
    """Profile creation model."""

    pass


class ProfileUpdate(ProfileBase):
    """Profile update model."""

    pass


class Profile(ProfileBase):
    """Complete profile model."""

    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic model configuration."""

        from_attributes = True
