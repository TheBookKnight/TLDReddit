"""Reddit API client schemas."""
from datetime import datetime

from pydantic import BaseModel, Field


class RedditComment(BaseModel):
    """A single Reddit comment."""

    reddit_id: str
    author: str | None = None
    body: str
    score: int = 0
    depth: int = 0


class RedditPost(BaseModel):
    """A single Reddit post."""

    reddit_id: str
    subreddit: str
    title: str
    body: str | None = None
    url: str | None = None
    score: int = 0
    num_comments: int = 0
    author: str | None = None
    permalink: str
    created_utc: datetime
    top_comments: list[RedditComment] = Field(default_factory=list)


class SubredditHotFeed(BaseModel):
    """A subreddit hot feed response."""

    subreddit: str
    posts: list[RedditPost] = Field(default_factory=list)
