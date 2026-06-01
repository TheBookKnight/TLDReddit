"""LLM analysis schemas and Pydantic models."""
from pydantic import BaseModel, Field, field_validator


class PostAnalysisResult(BaseModel):
    """LLM-generated analysis for a single Reddit post."""

    post_summary: str
    overall_sentiment: str = Field(
        ..., description="One of: positive, negative, neutral, mixed"
    )
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    key_community_takeaways: list[str] = Field(default_factory=list)
    bullish_arguments: list[str] = Field(default_factory=list)
    bearish_arguments: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("overall_sentiment")
    @classmethod
    def validate_sentiment(cls, v: str) -> str:
        allowed = {"positive", "negative", "neutral", "mixed"}
        normalized = v.lower().strip()
        if normalized not in allowed:
            raise ValueError(f"overall_sentiment must be one of {allowed}, got: {v!r}")
        return normalized


class SubredditAnalysisResult(BaseModel):
    """LLM-generated meta-analysis for an entire subreddit."""

    subreddit: str
    analysis_date: str
    major_themes: list[str] = Field(default_factory=list)
    emerging_topics: list[str] = Field(default_factory=list)
    community_sentiment: str
    community_sentiment_score: float = Field(ge=-1.0, le=1.0)
    notable_shifts: list[str] = Field(default_factory=list)
    summary: str

    @field_validator("community_sentiment")
    @classmethod
    def validate_sentiment(cls, v: str) -> str:
        allowed = {"positive", "negative", "neutral", "mixed"}
        normalized = v.lower().strip()
        if normalized not in allowed:
            raise ValueError(f"community_sentiment must be one of {allowed}, got: {v!r}")
        return normalized


class PostPayload(BaseModel):
    """Structured payload for LLM analysis of a post."""

    post_title: str
    post_body: str | None = None
    top_comments: list[str] = Field(default_factory=list)
