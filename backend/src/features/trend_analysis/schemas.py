"""Trend analysis response schemas."""
from pydantic import BaseModel, Field, RootModel


class TrendScorePoint(BaseModel):
    """Single point used in subreddit sentiment comparisons."""

    date: str = Field(description="Analysis date represented by the data point.", examples=["2024-01-15"])
    score: float | None = Field(
        description="Normalized sentiment score between -1 and 1 for that analysis date.",
        examples=[0.7],
    )


class CompareSentimentResponse(RootModel[dict[str, list[TrendScorePoint]]]):
    """Mapping of subreddit names to sentiment score series."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "stocks": [
                    {"date": "2024-01-01", "score": -0.3},
                    {"date": "2024-01-08", "score": 0.1},
                    {"date": "2024-01-15", "score": 0.7},
                ],
                "technology": [
                    {"date": "2024-01-01", "score": 0.2},
                    {"date": "2024-01-08", "score": 0.3},
                ],
            }
        }
    }


class SentimentTrendPoint(BaseModel):
    """Time-series sentiment point for a single subreddit."""

    date: str = Field(description="Analysis date represented by the data point.", examples=["2024-01-15"])
    community_sentiment: str | None = Field(
        description="Sentiment label assigned to the subreddit on that date.",
        examples=["positive"],
    )
    community_sentiment_score: float | None = Field(
        description="Normalized sentiment score between -1 and 1.",
        examples=[0.7],
    )


class ThemeTrendPoint(BaseModel):
    """Time-series themes for a single subreddit."""

    date: str = Field(description="Analysis date represented by the data point.", examples=["2024-01-15"])
    major_themes: list[str] = Field(
        default_factory=list,
        description="Top discussion themes identified for that date.",
        examples=[["Theme 3", "Tech"]],
    )
    emerging_topics: list[str] = Field(
        default_factory=list,
        description="New or growing topics identified for that date.",
        examples=[["Topic 3"]],
    )


class LatestTrendAnalysisResponse(BaseModel):
    """Latest aggregate analysis snapshot for a subreddit."""

    id: int = Field(description="Internal identifier for the stored analysis.", examples=[12])
    subreddit: str = Field(description="Canonical subreddit name without the r/ prefix.", examples=["stocks"])
    analysis_date: str = Field(description="Date represented by the analysis snapshot.", examples=["2024-01-15"])
    major_themes: list[str] = Field(
        default_factory=list,
        description="Top discussion themes identified in the latest analysis.",
        examples=[["Theme 3", "Tech"]],
    )
    emerging_topics: list[str] = Field(
        default_factory=list,
        description="New or accelerating topics found in the latest analysis.",
        examples=[["Topic 3"]],
    )
    community_sentiment: str | None = Field(
        description="Overall sentiment label for the latest analysis.",
        examples=["positive"],
    )
    community_sentiment_score: float | None = Field(
        description="Normalized sentiment score between -1 and 1.",
        examples=[0.7],
    )
    notable_shifts: list[str] = Field(
        default_factory=list,
        description="Meaningful changes compared with earlier subreddit analyses.",
        examples=[["Shift toward growth stocks"]],
    )
    summary: str | None = Field(
        description="Narrative summary of the latest subreddit analysis.",
        examples=["Analysis for 2024-01-15."],
    )
    created_at: str | None = Field(
        description="Timestamp when this analysis record was stored, serialized to ISO-8601.",
        examples=["2026-05-31T14:10:00+00:00"],
    )
