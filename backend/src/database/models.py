"""Database models for all features."""
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base


class Subreddit(Base):
    """Monitored subreddit configuration."""

    __tablename__ = "subreddits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    posts: Mapped[list["Post"]] = relationship("Post", back_populates="subreddit")
    analyses: Mapped[list["SubredditAnalysis"]] = relationship(
        "SubredditAnalysis", back_populates="subreddit"
    )
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(
        "AnalysisRun", back_populates="subreddit"
    )


class Post(Base):
    """Reddit post captured during ingestion."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reddit_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    subreddit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subreddits.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    num_comments: Mapped[int] = mapped_column(Integer, default=0)
    author: Mapped[str] = mapped_column(String(100), nullable=True)
    permalink: Mapped[str] = mapped_column(String(500), nullable=True)
    reddit_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    subreddit: Mapped["Subreddit"] = relationship("Subreddit", back_populates="posts")
    analysis: Mapped["PostAnalysis"] = relationship(
        "PostAnalysis", back_populates="post", uselist=False
    )


class PostAnalysis(Base):
    """LLM-generated analysis for a single post."""

    __tablename__ = "post_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"), nullable=False)
    analysis_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analysis_runs.id"), nullable=True
    )
    post_summary: Mapped[str] = mapped_column(Text, nullable=True)
    overall_sentiment: Mapped[str] = mapped_column(String(50), nullable=True)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=True)
    key_community_takeaways: Mapped[list] = mapped_column(JSON, nullable=True)
    bullish_arguments: Mapped[list] = mapped_column(JSON, nullable=True)
    bearish_arguments: Mapped[list] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    top_comments_raw: Mapped[list] = mapped_column(JSON, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    post: Mapped["Post"] = relationship("Post", back_populates="analysis")
    analysis_run: Mapped["AnalysisRun"] = relationship(
        "AnalysisRun", back_populates="post_analyses"
    )


class SubredditAnalysis(Base):
    """LLM-generated meta-analysis for an entire subreddit."""

    __tablename__ = "subreddit_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subreddit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subreddits.id"), nullable=False
    )
    analysis_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analysis_runs.id"), nullable=True
    )
    analysis_date: Mapped[str] = mapped_column(String(20), nullable=False)
    major_themes: Mapped[list] = mapped_column(JSON, nullable=True)
    emerging_topics: Mapped[list] = mapped_column(JSON, nullable=True)
    community_sentiment: Mapped[str] = mapped_column(String(50), nullable=True)
    community_sentiment_score: Mapped[float] = mapped_column(Float, nullable=True)
    notable_shifts: Mapped[list] = mapped_column(JSON, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    subreddit: Mapped["Subreddit"] = relationship("Subreddit", back_populates="analyses")
    analysis_run: Mapped["AnalysisRun"] = relationship(
        "AnalysisRun", back_populates="subreddit_analyses"
    )


class AnalysisRun(Base):
    """Record of a complete ingestion and analysis run."""

    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subreddit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subreddits.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="pending")
    posts_processed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    subreddit: Mapped["Subreddit"] = relationship("Subreddit", back_populates="analysis_runs")
    post_analyses: Mapped[list["PostAnalysis"]] = relationship(
        "PostAnalysis", back_populates="analysis_run"
    )
    subreddit_analyses: Mapped[list["SubredditAnalysis"]] = relationship(
        "SubredditAnalysis", back_populates="analysis_run"
    )


class ChatSession(Base):
    """A user chat session for exploring Reddit trend data."""

    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session"
    )


class ChatMessage(Base):
    """A single message in a chat session."""

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat_sessions.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user / assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    context_used: Mapped[list] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
