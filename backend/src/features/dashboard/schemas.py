"""Dashboard response schemas."""
from pydantic import BaseModel, Field


class DashboardOverviewItem(BaseModel):
    """High-level dashboard summary for one monitored subreddit."""

    id: int = Field(description="Internal identifier for the monitored subreddit.", examples=[3])
    name: str = Field(
        description="Canonical subreddit name without the r/ prefix.",
        examples=["stocks"],
    )
    display_name: str | None = Field(
        description="Optional display label shown in the dashboard.",
        examples=["r/stocks"],
    )
    latest_analysis_date: str | None = Field(
        description="Date string for the latest completed subreddit analysis.",
        examples=["2024-01-15"],
    )
    community_sentiment: str | None = Field(
        description="Latest overall community sentiment label.",
        examples=["positive"],
    )
    community_sentiment_score: float | None = Field(
        description="Latest normalized community sentiment score between -1 and 1.",
        examples=[0.65],
    )
    major_themes: list[str] = Field(
        default_factory=list,
        description="Top themes from the most recent subreddit analysis.",
        examples=[["Earnings", "Fed rates", "AI stocks"]],
    )
    summary: str | None = Field(
        description="Brief textual summary of the latest subreddit analysis.",
        examples=["r/stocks is bullish this week."],
    )


class DashboardOverviewResponse(BaseModel):
    """Overview response for the dashboard landing page."""

    subreddits: list[DashboardOverviewItem] = Field(
        default_factory=list,
        description="Active monitored subreddits included in the overview.",
    )
    total: int = Field(description="Number of subreddits returned in the overview.", examples=[1])

    model_config = {
        "json_schema_extra": {
            "example": {
                "subreddits": [
                    {
                        "id": 3,
                        "name": "stocks",
                        "display_name": "r/stocks",
                        "latest_analysis_date": "2024-01-15",
                        "community_sentiment": "positive",
                        "community_sentiment_score": 0.65,
                        "major_themes": ["Earnings", "Fed rates", "AI stocks"],
                        "summary": "r/stocks is bullish this week.",
                    }
                ],
                "total": 1,
            }
        }
    }


class DashboardSubredditSummary(BaseModel):
    """Basic subreddit metadata used by detailed dashboard views."""

    id: int = Field(description="Internal identifier for the monitored subreddit.", examples=[3])
    name: str = Field(
        description="Canonical subreddit name without the r/ prefix.",
        examples=["stocks"],
    )
    display_name: str | None = Field(
        description="Optional display label shown in the dashboard.",
        examples=["r/stocks"],
    )
    description: str | None = Field(
        description="Short explanation of why the subreddit is monitored.",
        examples=["Broad retail investor discussion and market sentiment."],
    )
    is_active: bool = Field(
        description="Whether the subreddit is currently enabled for ingestion.",
        examples=[True],
    )


class DashboardLatestAnalysis(BaseModel):
    """Latest aggregate analysis for a subreddit."""

    analysis_date: str = Field(
        description="Date represented by the analysis snapshot.",
        examples=["2024-01-15"],
    )
    major_themes: list[str] = Field(
        default_factory=list,
        description="Major themes identified in the subreddit conversation.",
        examples=[["Earnings", "Fed rates"]],
    )
    emerging_topics: list[str] = Field(
        default_factory=list,
        description="New or growing topics in recent subreddit activity.",
        examples=[["AI stocks"]],
    )
    community_sentiment: str | None = Field(
        description="Overall community sentiment label for the analysis period.",
        examples=["positive"],
    )
    community_sentiment_score: float | None = Field(
        description="Normalized community sentiment score between -1 and 1.",
        examples=[0.65],
    )
    notable_shifts: list[str] = Field(
        default_factory=list,
        description="Important changes observed relative to earlier discussions.",
        examples=[["Shift to growth"]],
    )
    summary: str | None = Field(
        description="Narrative summary of the latest subreddit analysis.",
        examples=["r/stocks is bullish this week."],
    )


class DashboardPostAnalysisSummary(BaseModel):
    """Condensed post analysis used inside dashboard post lists."""

    post_summary: str | None = Field(
        description="Short summary of the post discussion and comments.",
        examples=["Great discussion"],
    )
    overall_sentiment: str | None = Field(
        description="Overall sentiment label for the post discussion.",
        examples=["positive"],
    )
    sentiment_score: float | None = Field(
        description="Normalized sentiment score between -1 and 1.",
        examples=[0.8],
    )
    key_community_takeaways: list[str] = Field(
        default_factory=list,
        description="Most important conclusions expressed by commenters.",
        examples=[["Buy the dip"]],
    )
    bullish_arguments: list[str] = Field(
        default_factory=list,
        description="Arguments from commenters supporting a bullish view.",
        examples=[["Strong earnings"]],
    )
    bearish_arguments: list[str] = Field(
        default_factory=list,
        description="Arguments from commenters supporting a bearish view.",
        examples=[["High valuation"]],
    )
    confidence: float | None = Field(
        description="Confidence score for the generated analysis between 0 and 1.",
        examples=[0.9],
    )


class DashboardPostSummary(BaseModel):
    """Summarized post entry used in subreddit detail responses."""

    id: int = Field(description="Internal post identifier.", examples=[11])
    reddit_id: str = Field(description="Original Reddit post identifier.", examples=["post_stocks"])
    title: str = Field(description="Title of the Reddit post.", examples=["Test Post"])
    score: int = Field(description="Reddit score captured during ingestion.", examples=[100])
    num_comments: int = Field(
        description="Number of comments captured during ingestion.",
        examples=[10],
    )
    url: str | None = Field(
        description="External URL associated with the post, if any.",
        examples=[None],
    )
    permalink: str | None = Field(
        description="Reddit permalink for the captured post.",
        examples=["/r/stocks/comments/post_stocks/"],
    )
    reddit_created_at: str | None = Field(
        description="Original Reddit creation timestamp serialized to ISO-8601.",
        examples=["2026-05-31T14:00:00+00:00"],
    )
    analysis: DashboardPostAnalysisSummary | None = Field(
        description="Generated analysis for the post, if analysis has been completed.",
    )


class DashboardSubredditDetailResponse(BaseModel):
    """Detailed dashboard response for a single subreddit."""

    subreddit: DashboardSubredditSummary = Field(description="Requested subreddit metadata.")
    latest_analysis: DashboardLatestAnalysis | None = Field(
        description="Latest aggregate subreddit analysis, if available.",
    )
    posts: list[DashboardPostSummary] = Field(
        default_factory=list,
        description="Top recent posts returned for the subreddit.",
    )


class DashboardPostDetailAnalysis(DashboardPostAnalysisSummary):
    """Expanded post analysis used for the single-post detail view."""

    top_comments: list[str] = Field(
        default_factory=list,
        description="Top comments that were included in the analysis prompt.",
        examples=[["Management guidance looks strong.", "Valuation still seems stretched."]],
    )
    analyzed_at: str | None = Field(
        description="When the post analysis was generated, serialized to ISO-8601.",
        examples=["2026-05-31T14:10:00+00:00"],
    )


class DashboardPostDetailResponse(BaseModel):
    """Detailed response for a single monitored Reddit post."""

    id: int = Field(description="Internal post identifier.", examples=[11])
    reddit_id: str = Field(description="Original Reddit post identifier.", examples=["post_stocks"])
    title: str = Field(description="Title of the Reddit post.", examples=["Test Post"])
    body: str | None = Field(
        description="Self-post body text captured during ingestion, if present.",
        examples=["Investors are debating AI demand and earnings quality."],
    )
    score: int = Field(description="Reddit score captured during ingestion.", examples=[100])
    num_comments: int = Field(
        description="Number of comments captured during ingestion.",
        examples=[10],
    )
    url: str | None = Field(
        description="External URL associated with the post, if any.",
        examples=[None],
    )
    permalink: str | None = Field(
        description="Reddit permalink for the captured post.",
        examples=["/r/stocks/comments/post_stocks/"],
    )
    author: str | None = Field(
        description="Reddit username of the post author.",
        examples=["marketwatcher42"],
    )
    reddit_created_at: str | None = Field(
        description="Original Reddit creation timestamp serialized to ISO-8601.",
        examples=["2026-05-31T14:00:00+00:00"],
    )
    analysis: DashboardPostDetailAnalysis | None = Field(
        description="Generated analysis for the post, if analysis has been completed.",
    )
