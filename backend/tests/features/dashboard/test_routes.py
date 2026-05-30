"""Tests for the dashboard API routes."""
from datetime import UTC, datetime

import pytest
from src.database.models import (
    Post,
    PostAnalysis,
    SubredditAnalysis,
)
from src.database.models import Subreddit as SubredditModel


async def _create_subreddit_with_analysis(db_session, name="stocks"):
    """Helper to create a subreddit with a full analysis."""
    subreddit = SubredditModel(name=name, is_active=True)
    db_session.add(subreddit)
    await db_session.flush()

    post = Post(
        reddit_id=f"post_{name}",
        subreddit_id=subreddit.id,
        title="Test Post",
        score=100,
        num_comments=10,
        permalink=f"/r/{name}/comments/post_{name}/",
        reddit_created_at=datetime.now(UTC),
    )
    db_session.add(post)
    await db_session.flush()

    post_analysis = PostAnalysis(
        post_id=post.id,
        post_summary="Great discussion",
        overall_sentiment="positive",
        sentiment_score=0.8,
        key_community_takeaways=["Buy the dip"],
        bullish_arguments=["Strong earnings"],
        bearish_arguments=["High valuation"],
        confidence=0.9,
    )
    db_session.add(post_analysis)

    analysis = SubredditAnalysis(
        subreddit_id=subreddit.id,
        analysis_date="2024-01-15",
        major_themes=["Earnings", "Fed rates"],
        emerging_topics=["AI stocks"],
        community_sentiment="positive",
        community_sentiment_score=0.65,
        notable_shifts=["Shift to growth"],
        summary="r/stocks is bullish this week.",
    )
    db_session.add(analysis)
    await db_session.flush()

    return subreddit, post, analysis


@pytest.mark.asyncio
async def test_overview_empty(client):
    """Test overview with no subreddits."""
    response = await client.get("/api/v1/dashboard/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["subreddits"] == []


@pytest.mark.asyncio
async def test_overview_with_data(client, db_session):
    """Test overview with subreddits and analyses."""
    await _create_subreddit_with_analysis(db_session, "techtest")

    response = await client.get("/api/v1/dashboard/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["subreddits"][0]["name"] == "techtest"
    assert data["subreddits"][0]["community_sentiment"] == "positive"


@pytest.mark.asyncio
async def test_subreddit_detail(client, db_session):
    """Test subreddit detail view."""
    subreddit, post, analysis = await _create_subreddit_with_analysis(db_session, "detailtest")

    response = await client.get(f"/api/v1/dashboard/subreddit/{subreddit.name}")
    assert response.status_code == 200
    data = response.json()
    assert data["subreddit"]["name"] == subreddit.name
    assert data["latest_analysis"] is not None
    assert len(data["posts"]) == 1
    assert data["posts"][0]["title"] == "Test Post"


@pytest.mark.asyncio
async def test_subreddit_detail_not_found(client):
    """Test subreddit detail for non-existent subreddit."""
    response = await client.get("/api/v1/dashboard/subreddit/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_detail(client, db_session):
    """Test post detail view."""
    subreddit, post, _ = await _create_subreddit_with_analysis(db_session, "posttest")

    response = await client.get(f"/api/v1/dashboard/post/{post.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == post.id
    assert data["analysis"]["overall_sentiment"] == "positive"


@pytest.mark.asyncio
async def test_post_detail_not_found(client):
    """Test post detail for non-existent post."""
    response = await client.get("/api/v1/dashboard/post/99999")
    assert response.status_code == 404
