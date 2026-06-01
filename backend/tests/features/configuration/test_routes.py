"""Tests for the configuration (subreddits) API routes."""
from datetime import UTC, datetime

import pytest
from src.database.models import AnalysisRun, Post, PostAnalysis, SubredditAnalysis
from src.database.models import Subreddit as SubredditModel


@pytest.mark.asyncio
async def test_list_subreddits_empty(client):
    """Test listing subreddits when none exist."""
    response = await client.get("/api/v1/subreddits/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_subreddit(client):
    """Test creating a new subreddit."""
    response = await client.post(
        "/api/v1/subreddits/",
        json={"name": "Python", "display_name": "r/Python"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "python"
    assert data["display_name"] == "r/Python"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_duplicate_subreddit(client):
    """Test that creating a duplicate subreddit returns 409."""
    await client.post("/api/v1/subreddits/", json={"name": "duplicatetest"})
    response = await client.post("/api/v1/subreddits/", json={"name": "duplicatetest"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_duplicate_subreddit_case_insensitive(client):
    """Test that duplicate subreddit names are rejected regardless of case or prefix."""
    first = await client.post("/api/v1/subreddits/", json={"name": "Catholicism"})
    assert first.status_code == 201
    assert first.json()["name"] == "catholicism"

    response = await client.post("/api/v1/subreddits/", json={"name": "r/Catholicism"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_subreddit(client, sample_subreddit):
    """Test getting a specific subreddit."""
    response = await client.get(f"/api/v1/subreddits/{sample_subreddit.name}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_subreddit.name


@pytest.mark.asyncio
async def test_get_subreddit_not_found(client):
    """Test getting a non-existent subreddit returns 404."""
    response = await client.get("/api/v1/subreddits/doesnotexist")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_subreddit(client, sample_subreddit):
    """Test updating a subreddit."""
    response = await client.patch(
        f"/api/v1/subreddits/{sample_subreddit.name}",
        json={"display_name": "Updated Name", "is_active": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Name"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_delete_subreddit(client, sample_subreddit):
    """Test soft-deleting a subreddit."""
    response = await client.delete(f"/api/v1/subreddits/{sample_subreddit.name}")
    assert response.status_code == 204

    # Should not appear in active list
    list_response = await client.get("/api/v1/subreddits/")
    names = [s["name"] for s in list_response.json()]
    assert sample_subreddit.name not in names


@pytest.mark.asyncio
async def test_delete_all_subreddits_removes_related_data(client, db_session):
    """Test bulk delete removes subreddit configs and related stored analysis data."""
    subreddit = SubredditModel(name="cleanupsub", is_active=True)
    db_session.add(subreddit)
    await db_session.flush()

    run = AnalysisRun(subreddit_id=subreddit.id, status="completed", posts_processed=1)
    db_session.add(run)
    await db_session.flush()

    post = Post(
        reddit_id="cleanup-post",
        subreddit_id=subreddit.id,
        title="Cleanup Post",
        permalink="/r/cleanupsub/comments/cleanup-post/",
        reddit_created_at=datetime.now(UTC),
    )
    db_session.add(post)
    await db_session.flush()

    db_session.add(
        PostAnalysis(
            post_id=post.id,
            analysis_run_id=run.id,
            post_summary="Cleanup summary",
            overall_sentiment="neutral",
            sentiment_score=0.0,
            key_community_takeaways=[],
            bullish_arguments=[],
            bearish_arguments=[],
            confidence=0.5,
        )
    )
    db_session.add(
        SubredditAnalysis(
            subreddit_id=subreddit.id,
            analysis_run_id=run.id,
            analysis_date="2026-05-31",
            major_themes=["cleanup"],
            emerging_topics=[],
            community_sentiment="neutral",
            community_sentiment_score=0.0,
            notable_shifts=[],
            summary="Cleanup summary",
        )
    )
    await db_session.flush()

    response = await client.delete("/api/v1/subreddits/")

    assert response.status_code == 200
    assert response.json() == {"deleted_subreddits": 1}
    assert (await client.get("/api/v1/subreddits/?include_inactive=true")).json() == []


@pytest.mark.asyncio
async def test_list_subreddits_include_inactive(client, sample_subreddit):
    """Test listing subreddits including inactive ones."""
    await client.delete(f"/api/v1/subreddits/{sample_subreddit.name}")

    response = await client.get("/api/v1/subreddits/?include_inactive=true")
    assert response.status_code == 200
    names = [s["name"] for s in response.json()]
    assert sample_subreddit.name in names


@pytest.mark.asyncio
async def test_subreddit_name_validation(client):
    """Test that subreddit name validation rejects invalid characters."""
    response = await client.post(
        "/api/v1/subreddits/",
        json={"name": "invalid name!"},
    )
    assert response.status_code == 422
