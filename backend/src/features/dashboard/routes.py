"""Dashboard API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.base import get_session
from src.database.models import Post, SubredditAnalysis
from src.database.models import Subreddit as SubredditModel

router = APIRouter()


@router.get("/overview")
async def get_overview(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get an overview of all monitored subreddits with their latest analysis."""
    result = await session.execute(
        select(SubredditModel).where(SubredditModel.is_active.is_(True)).order_by(SubredditModel.name)
    )
    subreddits = result.scalars().all()

    overview = []
    for subreddit in subreddits:
        # Get latest analysis
        analysis_result = await session.execute(
            select(SubredditAnalysis)
            .where(SubredditAnalysis.subreddit_id == subreddit.id)
            .order_by(SubredditAnalysis.created_at.desc())
            .limit(1)
        )
        latest = analysis_result.scalar_one_or_none()

        overview.append(
            {
                "id": subreddit.id,
                "name": subreddit.name,
                "display_name": subreddit.display_name,
                "latest_analysis_date": latest.analysis_date if latest else None,
                "community_sentiment": latest.community_sentiment if latest else None,
                "community_sentiment_score": latest.community_sentiment_score if latest else None,
                "major_themes": (latest.major_themes or [])[:3] if latest else [],
                "summary": latest.summary if latest else None,
            }
        )

    return {"subreddits": overview, "total": len(overview)}


@router.get("/subreddit/{name}")
async def get_subreddit_detail(
    name: str,
    session: AsyncSession = Depends(get_session),
    posts_limit: int = Query(default=10, ge=1, le=50),
) -> dict:
    """Get detailed view for a specific subreddit."""
    result = await session.execute(
        select(SubredditModel).where(SubredditModel.name == name)
    )
    subreddit = result.scalar_one_or_none()
    if subreddit is None:
        raise HTTPException(status_code=404, detail=f"Subreddit '{name}' not found.")

    # Latest analysis
    analysis_result = await session.execute(
        select(SubredditAnalysis)
        .where(SubredditAnalysis.subreddit_id == subreddit.id)
        .order_by(SubredditAnalysis.created_at.desc())
        .limit(1)
    )
    latest = analysis_result.scalar_one_or_none()

    # Recent posts with analyses
    posts_result = await session.execute(
        select(Post)
        .where(Post.subreddit_id == subreddit.id)
        .order_by(Post.score.desc())
        .limit(posts_limit)
        .options(selectinload(Post.analysis))
    )
    posts = posts_result.scalars().all()

    def _post_dict(p: Post) -> dict:
        a = p.analysis
        return {
            "id": p.id,
            "reddit_id": p.reddit_id,
            "title": p.title,
            "score": p.score,
            "num_comments": p.num_comments,
            "url": p.url,
            "permalink": p.permalink,
            "reddit_created_at": p.reddit_created_at.isoformat() if p.reddit_created_at else None,
            "analysis": {
                "post_summary": a.post_summary,
                "overall_sentiment": a.overall_sentiment,
                "sentiment_score": a.sentiment_score,
                "key_community_takeaways": a.key_community_takeaways or [],
                "bullish_arguments": a.bullish_arguments or [],
                "bearish_arguments": a.bearish_arguments or [],
                "confidence": a.confidence,
            }
            if a
            else None,
        }

    return {
        "subreddit": {
            "id": subreddit.id,
            "name": subreddit.name,
            "display_name": subreddit.display_name,
            "description": subreddit.description,
            "is_active": subreddit.is_active,
        },
        "latest_analysis": {
            "analysis_date": latest.analysis_date,
            "major_themes": latest.major_themes or [],
            "emerging_topics": latest.emerging_topics or [],
            "community_sentiment": latest.community_sentiment,
            "community_sentiment_score": latest.community_sentiment_score,
            "notable_shifts": latest.notable_shifts or [],
            "summary": latest.summary,
        }
        if latest
        else None,
        "posts": [_post_dict(p) for p in posts],
    }


@router.get("/post/{post_id}")
async def get_post_detail(
    post_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get detailed view for a single post."""
    result = await session.execute(
        select(Post).where(Post.id == post_id).options(selectinload(Post.analysis))
    )
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found.")

    a = post.analysis
    return {
        "id": post.id,
        "reddit_id": post.reddit_id,
        "title": post.title,
        "body": post.body,
        "score": post.score,
        "num_comments": post.num_comments,
        "url": post.url,
        "permalink": post.permalink,
        "author": post.author,
        "reddit_created_at": post.reddit_created_at.isoformat() if post.reddit_created_at else None,
        "analysis": {
            "post_summary": a.post_summary,
            "overall_sentiment": a.overall_sentiment,
            "sentiment_score": a.sentiment_score,
            "key_community_takeaways": a.key_community_takeaways or [],
            "bullish_arguments": a.bullish_arguments or [],
            "bearish_arguments": a.bearish_arguments or [],
            "confidence": a.confidence,
            "top_comments": a.top_comments_raw or [],
            "analyzed_at": a.analyzed_at.isoformat() if a.analyzed_at else None,
        }
        if a
        else None,
    }
