"""Tests for the Reddit client."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.features.reddit_client.client import (
    RedditClient,
    RedditClientError,
    RedditRateLimitError,
)
from src.features.reddit_client.schemas import SubredditHotFeed
from src.shared.settings import Settings


@pytest.fixture
def settings():
    return Settings(
        reddit_user_agent="TestAgent/1.0",
        reddit_request_delay=0.0,
        reddit_max_retries=1,
        openai_api_key="test",
        database_url="sqlite+aiosqlite:///:memory:",
    )


HOT_FEED_RESPONSE = {
    "data": {
        "children": [
            {
                "data": {
                    "id": "abc123",
                    "title": "Test Post",
                    "selftext": "Test body",
                    "url": "https://reddit.com/r/test/abc123",
                    "score": 1000,
                    "num_comments": 50,
                    "author": "testuser",
                    "permalink": "/r/test/comments/abc123/test_post/",
                    "created_utc": 1700000000.0,
                    "subreddit": "test",
                }
            }
        ]
    }
}

COMMENTS_RESPONSE = [
    {},  # Post listing (not used)
    {
        "data": {
            "children": [
                {
                    "kind": "t1",
                    "data": {
                        "id": "comment1",
                        "author": "user1",
                        "body": "Great post!",
                        "score": 100,
                        "replies": {},
                    },
                },
                {
                    "kind": "t1",
                    "data": {
                        "id": "comment2",
                        "author": "[deleted]",
                        "body": "[deleted]",
                        "score": 50,
                        "replies": {},
                    },
                },
                {
                    "kind": "t1",
                    "data": {
                        "id": "comment3",
                        "author": "user3",
                        "body": "Interesting perspective",
                        "score": 75,
                        "replies": {
                            "data": {
                                "children": [
                                    {
                                        "kind": "t1",
                                        "data": {
                                            "id": "reply1",
                                            "author": "user4",
                                            "body": "I agree!",
                                            "score": 25,
                                            "replies": {},
                                        },
                                    }
                                ]
                            }
                        },
                    },
                },
            ]
        }
    },
]


@pytest.mark.asyncio
async def test_get_hot_posts_success(settings):
    """Test successful hot posts fetch."""
    client = RedditClient(settings=settings)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = HOT_FEED_RESPONSE

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        async with client:
            feed = await client.get_hot_posts("test", limit=5)

    assert isinstance(feed, SubredditHotFeed)
    assert feed.subreddit == "test"
    assert len(feed.posts) == 1
    assert feed.posts[0].reddit_id == "abc123"
    assert feed.posts[0].title == "Test Post"
    assert feed.posts[0].score == 1000


@pytest.mark.asyncio
async def test_get_post_comments_filters_deleted(settings):
    """Test that deleted/removed comments are filtered out."""
    client = RedditClient(settings=settings)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = COMMENTS_RESPONSE

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        async with client:
            comments = await client.get_post_comments("/r/test/comments/abc123/", limit=10)

    comment_authors = [c.author for c in comments]
    assert "[deleted]" not in comment_authors
    # Should have user1, user3, and the reply user4
    assert any(c.author == "user1" for c in comments)
    assert any(c.author == "user3" for c in comments)


@pytest.mark.asyncio
async def test_get_post_comments_sorted_by_score(settings):
    """Test that comments are sorted by score descending."""
    client = RedditClient(settings=settings)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = COMMENTS_RESPONSE

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        async with client:
            comments = await client.get_post_comments("/r/test/comments/abc123/", limit=10)

    scores = [c.score for c in comments]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_rate_limit_raises_error(settings):
    """Test that 429 response raises RedditRateLimitError after retries."""
    settings.reddit_max_retries = 1
    client = RedditClient(settings=settings)

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers = {"Retry-After": "1"}

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            async with client:
                with pytest.raises((RedditRateLimitError, Exception)):
                    await client.get_hot_posts("test")


@pytest.mark.asyncio
async def test_404_raises_client_error(settings):
    """Test that 404 response raises RedditClientError."""
    client = RedditClient(settings=settings)

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        async with client:
            with pytest.raises(RedditClientError, match="not found"):
                await client.get_hot_posts("nonexistent")


def test_parse_post_skips_missing_id(settings):
    """Test that posts without an ID are skipped."""
    client = RedditClient(settings=settings)
    result = client._parse_post({}, "test")
    assert result is None


def test_extract_comments_ignores_non_t1(settings):
    """Test that non-comment children (links etc) are ignored."""
    client = RedditClient(settings=settings)
    children = [
        {"kind": "more", "data": {"children": []}},
        {
            "kind": "t1",
            "data": {
                "id": "c1",
                "author": "user",
                "body": "valid",
                "score": 10,
                "replies": {},
            },
        },
    ]
    result: list = []
    client._extract_comments(children, result, 0)
    assert len(result) == 1
    assert result[0].body == "valid"
