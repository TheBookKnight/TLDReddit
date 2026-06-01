"""Subreddit ingestion response schemas."""
from pydantic import BaseModel, Field


class IngestionTriggerResponse(BaseModel):
    """Accepted response for a single subreddit ingestion request."""

    message: str = Field(
        description="Human-readable confirmation that the ingestion job was queued.",
        examples=["Ingestion started for r/stocks"],
    )
    subreddit: str = Field(
        description="Canonical subreddit name that was queued for ingestion.",
        examples=["stocks"],
    )


class IngestionTriggerAllResponse(BaseModel):
    """Accepted response for a run-all ingestion request."""

    message: str = Field(
        description="Human-readable confirmation summarizing how many jobs were queued.",
        examples=["Ingestion started for 2 subreddits"],
    )
    subreddits: list[str] = Field(
        default_factory=list,
        description="Subreddit names that were queued for ingestion.",
        examples=[["stocks", "technology"]],
    )


class AnalysisRunResponse(BaseModel):
    """Recorded ingestion and analysis run for a subreddit."""

    id: int = Field(description="Internal identifier for the analysis run.", examples=[21])
    status: str = Field(
        description="Current run status such as pending, running, completed, or failed.",
        examples=["completed"],
    )
    posts_processed: int = Field(
        description="Number of posts processed during the run.",
        examples=[25],
    )
    started_at: str | None = Field(
        description="Timestamp when the run started, serialized to ISO-8601.",
        examples=["2026-05-31T14:00:00+00:00"],
    )
    completed_at: str | None = Field(
        description="Timestamp when the run completed, serialized to ISO-8601.",
        examples=["2026-05-31T14:03:00+00:00"],
    )
    error_message: str | None = Field(
        description="Failure detail captured for a run that did not complete successfully.",
        examples=[None],
    )
