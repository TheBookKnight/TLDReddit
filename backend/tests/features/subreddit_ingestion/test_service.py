"""Tests for the ingestion pipeline service."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from src.database.models import Post
from src.database.models import Subreddit as SubredditModel
from src.features.post_analysis.schemas import PostAnalysisResult, SubredditAnalysisResult
from src.features.reddit_client.schemas import RedditComment, RedditPost, SubredditHotFeed
from src.features.subreddit_ingestion.service import IngestionService
from src.shared.settings import Settings


@pytest.fixture
def settings():
    return Settings(
        ingestion_top_posts=2,
        ingestion_top_comments=5,
        openai_api_key="test",
        database_url="sqlite+aiosqlite:///:memory:",
        reddit_request_delay=0.0,
    )


def make_reddit_post(reddit_id="post1"):
    return RedditPost(
        reddit_id=reddit_id,
        subreddit="testsubreddit",
        title=f"Test Post {reddit_id}",
        body="Test body",
        url="https://reddit.com",
        score=100,
        num_comments=10,
        author="testuser",
        permalink=f"/r/testsubreddit/comments/{reddit_id}/",
        created_utc=datetime.now(UTC),
    )


def make_post_analysis_result():
    return PostAnalysisResult(
        post_summary="Great discussion about testing.",
        overall_sentiment="positive",
        sentiment_score=0.8,
        key_community_takeaways=["Testing is important"],
        bullish_arguments=["Good approach"],
        bearish_arguments=[],
        confidence=0.9,
    )


def make_subreddit_analysis_result(subreddit="testsubreddit"):
    return SubredditAnalysisResult(
        subreddit=subreddit,
        analysis_date="2024-01-01",
        major_themes=["Testing", "Development"],
        emerging_topics=["CI/CD"],
        community_sentiment="positive",
        community_sentiment_score=0.7,
        notable_shifts=[],
        summary="A community focused on development.",
    )


@pytest.mark.asyncio
async def test_run_for_subreddit_success(db_session, settings):
    """Test successful ingestion run for a subreddit."""
    subreddit = SubredditModel(name="testsubreddit", is_active=True)
    db_session.add(subreddit)
    await db_session.flush()

    mock_reddit = AsyncMock()
    mock_reddit.get_hot_posts.return_value = SubredditHotFeed(
        subreddit="testsubreddit",
        posts=[make_reddit_post("p1"), make_reddit_post("p2")],
    )
    mock_reddit.get_post_comments.return_value = [
        RedditComment(reddit_id="c1", author="user1", body="Comment 1", score=10)
    ]

    mock_llm = AsyncMock()
    mock_llm.analyze_post.return_value = make_post_analysis_result()
    mock_llm.analyze_subreddit.return_value = make_subreddit_analysis_result()

    svc = IngestionService(db_session, mock_reddit, mock_llm, settings)
    run = await svc.run_for_subreddit("testsubreddit")

    assert run.status == "completed"
    assert run.posts_processed == 2
    assert mock_reddit.get_hot_posts.called
    assert mock_reddit.get_post_comments.call_count == 2
    assert mock_llm.analyze_post.call_count == 2
    assert mock_llm.analyze_subreddit.call_count == 1


@pytest.mark.asyncio
async def test_run_for_subreddit_not_found(db_session, settings):
    """Test that ingestion fails gracefully for unknown subreddit."""
    mock_reddit = AsyncMock()
    mock_llm = AsyncMock()

    svc = IngestionService(db_session, mock_reddit, mock_llm, settings)
    with pytest.raises(ValueError, match="not found"):
        await svc.run_for_subreddit("nonexistent")


@pytest.mark.asyncio
async def test_run_for_subreddit_handles_llm_failure(db_session, settings):
    """Test that individual post LLM failures don't abort the whole run."""
    subreddit = SubredditModel(name="failsubreddit", is_active=True)
    db_session.add(subreddit)
    await db_session.flush()

    mock_reddit = AsyncMock()
    mock_reddit.get_hot_posts.return_value = SubredditHotFeed(
        subreddit="failsubreddit",
        posts=[make_reddit_post("p1")],
    )
    mock_reddit.get_post_comments.return_value = []

    mock_llm = AsyncMock()
    mock_llm.analyze_post.side_effect = ValueError("LLM error")
    mock_llm.analyze_subreddit.return_value = make_subreddit_analysis_result("failsubreddit")

    svc = IngestionService(db_session, mock_reddit, mock_llm, settings)
    run = await svc.run_for_subreddit("failsubreddit")

    # Run still completes (with 0 summaries but meta-analysis skipped gracefully)
    assert run.status == "completed"


@pytest.mark.asyncio
async def test_run_skips_existing_posts(db_session, settings):
    """Test that existing posts are updated, not duplicated."""
    subreddit = SubredditModel(name="updatesubreddit", is_active=True)
    db_session.add(subreddit)
    await db_session.flush()

    existing_post = Post(
        reddit_id="existing1",
        subreddit_id=subreddit.id,
        title="Old title",
        score=50,
        num_comments=5,
        permalink="/r/updatesubreddit/comments/existing1/",
        reddit_created_at=datetime.now(UTC),
    )
    db_session.add(existing_post)
    await db_session.flush()

    mock_reddit = AsyncMock()
    mock_reddit.get_hot_posts.return_value = SubredditHotFeed(
        subreddit="updatesubreddit",
        posts=[
            RedditPost(
                reddit_id="existing1",
                subreddit="updatesubreddit",
                title="Old title",
                score=200,  # Updated score
                num_comments=25,
                author="testuser",
                permalink="/r/updatesubreddit/comments/existing1/",
                created_utc=datetime.now(UTC),
            )
        ],
    )
    mock_reddit.get_post_comments.return_value = []
    mock_llm = AsyncMock()
    mock_llm.analyze_post.return_value = make_post_analysis_result()
    mock_llm.analyze_subreddit.return_value = make_subreddit_analysis_result("updatesubreddit")

    svc = IngestionService(db_session, mock_reddit, mock_llm, settings)
    await svc.run_for_subreddit("updatesubreddit")

    # Score should be updated
    await db_session.refresh(existing_post)
    assert existing_post.score == 200
