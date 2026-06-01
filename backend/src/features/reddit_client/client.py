"""Reddit HTTP client with retry handling and rate limiting."""
import asyncio
import logging
from datetime import UTC, datetime

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.features.reddit_client.schemas import RedditComment, RedditPost, SubredditHotFeed
from src.shared.settings import get_settings

logger = logging.getLogger(__name__)

_DELETED = {"[deleted]", "[removed]"}


class RedditClientError(Exception):
    """Base exception for Reddit client errors."""


class RedditRateLimitError(RedditClientError):
    """Raised when Reddit rate limit is hit."""


class RedditClient:
    """Async Reddit API client using JSON endpoints."""

    BASE_URL = "https://www.reddit.com"

    def __init__(self, settings=None) -> None:
        self._settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "RedditClient":
        self._client = httpx.AsyncClient(
            headers={"User-Agent": self._settings.reddit_user_agent},
            follow_redirects=True,
            timeout=30.0,
        )
        return self

    async def __aexit__(self, *_) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @retry(
        retry=retry_if_exception_type(RedditRateLimitError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _get(self, url: str, params: dict | None = None) -> dict:
        """Make an authenticated GET request with retry logic."""
        if self._client is None:
            raise RedditClientError("Client not initialized. Use as async context manager.")

        await asyncio.sleep(self._settings.reddit_request_delay)

        response = await self._client.get(url, params=params)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            logger.warning("Rate limited by Reddit, waiting %s seconds", retry_after)
            await asyncio.sleep(retry_after)
            raise RedditRateLimitError("Rate limited")

        if response.status_code == 404:
            raise RedditClientError(f"Subreddit or post not found: {url}")

        response.raise_for_status()
        return response.json()

    async def get_hot_posts(
        self, subreddit: str, limit: int = 10
    ) -> SubredditHotFeed:
        """Fetch hot posts from a subreddit."""
        url = f"{self.BASE_URL}/r/{subreddit}/hot.json"
        data = await self._get(url, params={"limit": limit, "raw_json": 1})

        posts = []
        for child in data.get("data", {}).get("children", []):
            post_data = child.get("data", {})
            post = self._parse_post(post_data, subreddit)
            if post:
                posts.append(post)

        return SubredditHotFeed(subreddit=subreddit, posts=posts[:limit])

    async def get_post_comments(
        self, permalink: str, limit: int = 20
    ) -> list[RedditComment]:
        """Fetch top comments for a post."""
        url = f"{self.BASE_URL}{permalink}.json"
        data = await self._get(url, params={"limit": 100, "sort": "top", "raw_json": 1})

        if not isinstance(data, list) or len(data) < 2:
            return []

        comments_listing = data[1]
        raw_comments = comments_listing.get("data", {}).get("children", [])

        comments: list[RedditComment] = []
        self._extract_comments(raw_comments, comments, depth=0)

        # Sort by score descending, take top N
        comments.sort(key=lambda c: c.score, reverse=True)
        return comments[:limit]

    def _extract_comments(
        self,
        children: list[dict],
        result: list[RedditComment],
        depth: int,
    ) -> None:
        """Recursively extract comments, skipping deleted/removed."""
        for child in children:
            kind = child.get("kind")
            if kind != "t1":
                continue

            data = child.get("data", {})
            body = data.get("body", "")
            author = data.get("author", "")

            if body in _DELETED or author in _DELETED or not body:
                continue

            comment = RedditComment(
                reddit_id=data.get("id", ""),
                author=author or None,
                body=body,
                score=data.get("score", 0),
                depth=depth,
            )
            result.append(comment)

            # Recurse into replies
            replies = data.get("replies", {})
            if isinstance(replies, dict):
                reply_children = replies.get("data", {}).get("children", [])
                self._extract_comments(reply_children, result, depth + 1)

    def _parse_post(self, data: dict, subreddit: str) -> RedditPost | None:
        """Parse raw post data into a RedditPost schema."""
        if not data.get("id"):
            return None

        created_utc = datetime.fromtimestamp(data.get("created_utc", 0), tz=UTC)

        return RedditPost(
            reddit_id=data["id"],
            subreddit=subreddit,
            title=data.get("title", ""),
            body=data.get("selftext") or None,
            url=data.get("url"),
            score=data.get("score", 0),
            num_comments=data.get("num_comments", 0),
            author=data.get("author"),
            permalink=data.get("permalink", ""),
            created_utc=created_utc,
        )
