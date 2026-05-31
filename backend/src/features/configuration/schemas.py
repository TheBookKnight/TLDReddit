"""Subreddit configuration schemas."""
from datetime import datetime

from pydantic import BaseModel, Field


class SubredditCreate(BaseModel):
    """Schema for creating a subreddit."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9_]+$",
        description="Canonical subreddit name without the r/ prefix.",
        examples=["stocks"],
    )
    display_name: str | None = Field(
        default=None,
        description="Optional UI label shown in dashboards and settings.",
        examples=["r/stocks"],
    )
    description: str | None = Field(
        default=None,
        description="Short note describing why this subreddit is monitored.",
        examples=["Broad retail investor discussion and market sentiment."],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "stocks",
                "display_name": "r/stocks",
                "description": "Broad retail investor discussion and market sentiment.",
            }
        }
    }


class SubredditUpdate(BaseModel):
    """Schema for updating a subreddit."""

    display_name: str | None = Field(
        default=None,
        description="Updated UI label for the subreddit.",
        examples=["r/stocks community"],
    )
    description: str | None = Field(
        default=None,
        description="Updated purpose or context for monitoring the subreddit.",
        examples=["Tracks retail investor discussion and daily trading themes."],
    )
    is_active: bool | None = Field(
        default=None,
        description="Whether the ingestion pipeline should continue monitoring this subreddit.",
        examples=[True],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "display_name": "r/stocks community",
                "description": "Tracks retail investor discussion and daily trading themes.",
                "is_active": True
            }
        }
    }


class SubredditResponse(BaseModel):
    """Subreddit response schema."""

    id: int = Field(description="Internal identifier for the configured subreddit.", examples=[3])
    name: str = Field(description="Canonical subreddit name without the r/ prefix.", examples=["stocks"])
    display_name: str | None = Field(
        description="UI-facing display name.",
        examples=["r/stocks"],
    )
    description: str | None = Field(
        description="Short explanation of what this subreddit covers.",
        examples=["Broad retail investor discussion and market sentiment."],
    )
    is_active: bool = Field(
        description="Whether ingestion and analysis remain enabled for this subreddit.",
        examples=[True],
    )
    created_at: datetime = Field(
        description="When the subreddit configuration was created in UTC.",
        examples=["2026-05-30T09:15:00Z"],
    )
    updated_at: datetime = Field(
        description="When the subreddit configuration was last updated in UTC.",
        examples=["2026-05-31T08:00:00Z"],
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 3,
                "name": "stocks",
                "display_name": "r/stocks",
                "description": "Broad retail investor discussion and market sentiment.",
                "is_active": True,
                "created_at": "2026-05-30T09:15:00Z",
                "updated_at": "2026-05-31T08:00:00Z",
            }
        },
    }
