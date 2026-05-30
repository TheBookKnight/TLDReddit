"""RAG-style retrieval service for chat."""
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Subreddit as SubredditModel
from src.database.models import SubredditAnalysis

logger = logging.getLogger(__name__)


async def retrieve_context(
    question: str,
    session: AsyncSession,
    days: int = 30,
    max_items: int = 10,
) -> list[dict]:
    """Retrieve relevant analyses from the database to answer the question.

    This is a keyword-based retrieval layer. Future enhancement: replace with
    vector embeddings for semantic similarity search.
    """
    cutoff = datetime.now(UTC) - timedelta(days=days)
    context_items: list[dict] = []

    # Find subreddit mentions in the question
    mentioned_subreddits = await _find_mentioned_subreddits(question, session)

    if mentioned_subreddits:
        # Retrieve analyses for specifically mentioned subreddits
        for subreddit in mentioned_subreddits:
            analyses = await session.execute(
                select(SubredditAnalysis)
                .where(
                    SubredditAnalysis.subreddit_id == subreddit.id,
                    SubredditAnalysis.created_at >= cutoff,
                )
                .order_by(SubredditAnalysis.created_at.desc())
                .limit(max_items // max(len(mentioned_subreddits), 1))
            )
            for a in analyses.scalars().all():
                context_items.append(
                    {
                        "type": "subreddit_analysis",
                        "subreddit": subreddit.name,
                        "date": a.analysis_date,
                        "summary": a.summary,
                        "major_themes": a.major_themes or [],
                        "emerging_topics": a.emerging_topics or [],
                        "community_sentiment": a.community_sentiment,
                        "community_sentiment_score": a.community_sentiment_score,
                        "notable_shifts": a.notable_shifts or [],
                    }
                )
    else:
        # General question: retrieve latest analyses from all subreddits
        analyses = await session.execute(
            select(SubredditAnalysis, SubredditModel)
            .join(SubredditModel, SubredditAnalysis.subreddit_id == SubredditModel.id)
            .where(SubredditAnalysis.created_at >= cutoff)
            .order_by(SubredditAnalysis.created_at.desc())
            .limit(max_items)
        )
        for analysis, subreddit in analyses.all():
            context_items.append(
                {
                    "type": "subreddit_analysis",
                    "subreddit": subreddit.name,
                    "date": analysis.analysis_date,
                    "summary": analysis.summary,
                    "major_themes": analysis.major_themes or [],
                    "emerging_topics": analysis.emerging_topics or [],
                    "community_sentiment": analysis.community_sentiment,
                    "community_sentiment_score": analysis.community_sentiment_score,
                }
            )

    return context_items[:max_items]


async def _find_mentioned_subreddits(
    question: str, session: AsyncSession
) -> list[SubredditModel]:
    """Find subreddits mentioned in the question (by name or r/ prefix)."""
    result = await session.execute(select(SubredditModel))
    all_subreddits = result.scalars().all()

    question_lower = question.lower()
    mentioned = []
    for sr in all_subreddits:
        if sr.name.lower() in question_lower or f"r/{sr.name.lower()}" in question_lower:
            mentioned.append(sr)

    return mentioned


def build_chat_prompt(question: str, context_items: list[dict]) -> str:
    """Build the full prompt for the LLM chat completion."""
    if not context_items:
        context_text = "No relevant data found in the database for the specified time range."
    else:
        parts = []
        for item in context_items:
            if item["type"] == "subreddit_analysis":
                part = (
                    f"r/{item['subreddit']} ({item['date']}):\n"
                    f"  Summary: {item.get('summary', 'N/A')}\n"
                    f"  Sentiment: {item.get('community_sentiment', 'N/A')} "
                    f"(score: {item.get('community_sentiment_score', 'N/A')})\n"
                    f"  Major Themes: {', '.join(item.get('major_themes', []))}\n"
                    f"  Emerging Topics: {', '.join(item.get('emerging_topics', []))}\n"
                )
                if item.get("notable_shifts"):
                    part += f"  Notable Shifts: {', '.join(item['notable_shifts'])}\n"
                parts.append(part)
        context_text = "\n".join(parts)

    return (
        "You are a Reddit trend analyst. You have access to the following data from "
        "analyzed Reddit discussions. Answer the user's question based only on this data.\n\n"
        f"=== Available Data ===\n{context_text}\n\n"
        f"=== User Question ===\n{question}"
    )
