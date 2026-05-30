"""Tests for the trend analysis API routes."""

import pytest
from src.database.models import Subreddit as SubredditModel
from src.database.models import SubredditAnalysis


async def _setup_trend_data(db_session, name="trendtest"):
    """Set up a subreddit with multiple analyses for trend testing."""
    subreddit = SubredditModel(name=name, is_active=True)
    db_session.add(subreddit)
    await db_session.flush()

    for i, (date, score, sentiment) in enumerate(
        [
            ("2024-01-01", -0.3, "negative"),
            ("2024-01-08", 0.1, "neutral"),
            ("2024-01-15", 0.7, "positive"),
        ]
    ):
        analysis = SubredditAnalysis(
            subreddit_id=subreddit.id,
            analysis_date=date,
            major_themes=[f"Theme {i+1}", "Tech"],
            emerging_topics=[f"Topic {i+1}"],
            community_sentiment=sentiment,
            community_sentiment_score=score,
            notable_shifts=[],
            summary=f"Analysis for {date}.",
        )
        db_session.add(analysis)

    await db_session.flush()
    return subreddit


@pytest.mark.asyncio
async def test_get_sentiment_trend(client, db_session):
    """Test getting sentiment trend for a subreddit."""
    subreddit = await _setup_trend_data(db_session, "sentimenttest")

    response = await client.get(f"/api/v1/trends/{subreddit.name}/sentiment?days=365")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    scores = [d["community_sentiment_score"] for d in data]
    assert scores == [-0.3, 0.1, 0.7]


@pytest.mark.asyncio
async def test_get_themes_over_time(client, db_session):
    """Test getting themes over time."""
    subreddit = await _setup_trend_data(db_session, "themestest")

    response = await client.get(f"/api/v1/trends/{subreddit.name}/themes?days=365")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    # Each item should have themes
    assert all("major_themes" in d for d in data)


@pytest.mark.asyncio
async def test_get_latest_analysis(client, db_session):
    """Test getting the latest analysis for a subreddit."""
    subreddit = await _setup_trend_data(db_session, "latesttest")

    response = await client.get(f"/api/v1/trends/{subreddit.name}/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_date"] == "2024-01-15"
    assert data["community_sentiment"] == "positive"


@pytest.mark.asyncio
async def test_get_latest_analysis_no_data(client, db_session):
    """Test latest analysis returns 404 when no data exists."""
    subreddit = SubredditModel(name="emptysubreddit", is_active=True)
    db_session.add(subreddit)
    await db_session.flush()

    response = await client.get("/api/v1/trends/emptysubreddit/latest")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_compare_sentiment(client, db_session):
    """Test comparing sentiment across multiple subreddits."""
    await _setup_trend_data(db_session, "compare1")
    await _setup_trend_data(db_session, "compare2")

    response = await client.get(
        "/api/v1/trends/compare/sentiment?subreddits=compare1&subreddits=compare2&days=365"
    )
    assert response.status_code == 200
    data = response.json()
    assert "compare1" in data
    assert "compare2" in data
    assert len(data["compare1"]) == 3


@pytest.mark.asyncio
async def test_sentiment_trend_not_found(client):
    """Test sentiment trend for non-existent subreddit."""
    response = await client.get("/api/v1/trends/doesnotexist/sentiment")
    assert response.status_code == 404
