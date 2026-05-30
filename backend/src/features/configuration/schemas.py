"""Subreddit configuration schemas."""
from datetime import datetime

from pydantic import BaseModel, Field


class SubredditCreate(BaseModel):
    """Schema for creating a subreddit."""

    name: str = Field(..., min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_]+$")
    display_name: str | None = None
    description: str | None = None


class SubredditUpdate(BaseModel):
    """Schema for updating a subreddit."""

    display_name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class SubredditResponse(BaseModel):
    """Subreddit response schema."""

    id: int
    name: str
    display_name: str | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
