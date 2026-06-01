"""Tests for chatbot retrieval service."""

import pytest
from src.database.models import Subreddit as SubredditModel
from src.database.models import SubredditAnalysis
from src.features.chatbot.retrieval import (
    _find_mentioned_subreddits,
    build_chat_prompt,
    retrieve_context,
)


async def _seed_subreddit_analysis(db_session, name, date="2024-01-15"):
    subreddit = SubredditModel(name=name, is_active=True)
    db_session.add(subreddit)
    await db_session.flush()

    analysis = SubredditAnalysis(
        subreddit_id=subreddit.id,
        analysis_date=date,
        major_themes=["Theme A"],
        emerging_topics=["Topic B"],
        community_sentiment="positive",
        community_sentiment_score=0.5,
        notable_shifts=[],
        summary=f"Summary for {name}.",
    )
    db_session.add(analysis)
    await db_session.flush()
    return subreddit


@pytest.mark.asyncio
async def test_find_mentioned_subreddits_by_name(db_session):
    """Test finding subreddits mentioned in a question by name."""
    await _seed_subreddit_analysis(db_session, "Catholicism")
    await _seed_subreddit_analysis(db_session, "stocks")

    result = await _find_mentioned_subreddits(
        "What has r/Catholicism been discussing?", db_session
    )
    names = [sr.name for sr in result]
    assert "Catholicism" in names
    assert "stocks" not in names


@pytest.mark.asyncio
async def test_find_mentioned_subreddits_case_insensitive(db_session):
    """Test case-insensitive subreddit matching."""
    await _seed_subreddit_analysis(db_session, "MachineLearning")

    result = await _find_mentioned_subreddits(
        "what is machinelearning discussing?", db_session
    )
    names = [sr.name for sr in result]
    assert "MachineLearning" in names


@pytest.mark.asyncio
async def test_retrieve_context_general_question(db_session):
    """Test context retrieval for a general question (no specific subreddit)."""
    await _seed_subreddit_analysis(db_session, "generaltest")

    context = await retrieve_context("What are the trending topics?", db_session, days=365)
    assert len(context) >= 1
    assert context[0]["type"] == "subreddit_analysis"


@pytest.mark.asyncio
async def test_retrieve_context_specific_subreddit(db_session):
    """Test context retrieval for a specific subreddit question."""
    await _seed_subreddit_analysis(db_session, "specifictest")
    await _seed_subreddit_analysis(db_session, "othertest")

    context = await retrieve_context(
        "What has r/specifictest been discussing?", db_session, days=365
    )
    subreddits = [c["subreddit"] for c in context]
    assert "specifictest" in subreddits


def test_build_chat_prompt_with_context():
    """Test chat prompt building with context items."""
    context = [
        {
            "type": "subreddit_analysis",
            "subreddit": "test",
            "date": "2024-01-01",
            "summary": "Active community.",
            "major_themes": ["AI", "Tech"],
            "emerging_topics": ["LLMs"],
            "community_sentiment": "positive",
            "community_sentiment_score": 0.8,
            "notable_shifts": [],
        }
    ]
    prompt = build_chat_prompt("What is r/test about?", context)
    assert "r/test" in prompt
    assert "Active community." in prompt
    assert "AI" in prompt


def test_build_chat_prompt_no_context():
    """Test chat prompt building with no context."""
    prompt = build_chat_prompt("What's trending?", [])
    assert "No relevant data" in prompt
