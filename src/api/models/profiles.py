"""User profile models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User role enumeration."""

    USER = "user"
    ADMIN = "admin"


class ProfileBase(BaseModel):
    """Base profile model."""

    name: Optional[str] = None
    avatar_url: Optional[str] = None
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
