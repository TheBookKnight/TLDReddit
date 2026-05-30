"""Trend analysis API routes."""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.base import get_session
from src.database.models import Subreddit as SubredditModel
from src.database.models import SubredditAnalysis

router = APIRouter()


@router.get("/compare/sentiment")
async def compare_sentiment(
    subreddits: list[str] = Query(...),
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Compare sentiment scores across multiple subreddits."""
    cutoff = datetime.now(UTC) - timedelta(days=days)
    result: dict[str, list[dict]] = {}

    for name in subreddits:
        sr_result = await session.execute(
            select(SubredditModel).where(SubredditModel.name == name)
        )
        subreddit = sr_result.scalar_one_or_none()
        if subreddit is None:
            result[name] = []
            continue

        analyses_result = await session.execute(
            select(SubredditAnalysis)
            .where(
                SubredditAnalysis.subreddit_id == subreddit.id,
                SubredditAnalysis.created_at >= cutoff,
            )
            .order_by(SubredditAnalysis.analysis_date.asc())
        )
        analyses = analyses_result.scalars().all()
        result[name] = [
            {
                "date": a.analysis_date,
                "score": a.community_sentiment_score,
            }
            for a in analyses
        ]

    return result


@router.get("/{subreddit_name}/sentiment")
async def get_sentiment_trend(
    subreddit_name: str,
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Get sentiment score trend over time for a subreddit."""
    result = await session.execute(
        select(SubredditModel).where(SubredditModel.name == subreddit_name)
    )
    subreddit = result.scalar_one_or_none()
    if subreddit is None:
        raise HTTPException(status_code=404, detail=f"Subreddit '{subreddit_name}' not found.")

    cutoff = datetime.now(UTC) - timedelta(days=days)
    analyses_result = await session.execute(
        select(SubredditAnalysis)
        .where(
            SubredditAnalysis.subreddit_id == subreddit.id,
            SubredditAnalysis.created_at >= cutoff,
        )
        .order_by(SubredditAnalysis.analysis_date.asc())
    )
    analyses = analyses_result.scalars().all()

    return [
        {
            "date": a.analysis_date,
            "community_sentiment": a.community_sentiment,
            "community_sentiment_score": a.community_sentiment_score,
        }
        for a in analyses
    ]


@router.get("/{subreddit_name}/themes")
async def get_themes_over_time(
    subreddit_name: str,
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Get major themes over time for a subreddit."""
    result = await session.execute(
        select(SubredditModel).where(SubredditModel.name == subreddit_name)
    )
    subreddit = result.scalar_one_or_none()
    if subreddit is None:
        raise HTTPException(status_code=404, detail=f"Subreddit '{subreddit_name}' not found.")

    cutoff = datetime.now(UTC) - timedelta(days=days)
    analyses_result = await session.execute(
        select(SubredditAnalysis)
        .where(
            SubredditAnalysis.subreddit_id == subreddit.id,
            SubredditAnalysis.created_at >= cutoff,
        )
        .order_by(SubredditAnalysis.analysis_date.asc())
    )
    analyses = analyses_result.scalars().all()

    return [
        {
            "date": a.analysis_date,
            "major_themes": a.major_themes or [],
            "emerging_topics": a.emerging_topics or [],
        }
        for a in analyses
    ]


@router.get("/{subreddit_name}/latest")
async def get_latest_analysis(
    subreddit_name: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get the most recent subreddit analysis."""
    result = await session.execute(
        select(SubredditModel).where(SubredditModel.name == subreddit_name)
    )
    subreddit = result.scalar_one_or_none()
    if subreddit is None:
        raise HTTPException(status_code=404, detail=f"Subreddit '{subreddit_name}' not found.")

    analysis_result = await session.execute(
        select(SubredditAnalysis)
        .where(SubredditAnalysis.subreddit_id == subreddit.id)
        .order_by(SubredditAnalysis.analysis_date.desc())
        .limit(1)
    )
    analysis = analysis_result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail=f"No analysis found for r/{subreddit_name}.",
        )

    return {
        "id": analysis.id,
        "subreddit": subreddit.name,
        "analysis_date": analysis.analysis_date,
        "major_themes": analysis.major_themes or [],
        "emerging_topics": analysis.emerging_topics or [],
        "community_sentiment": analysis.community_sentiment,
        "community_sentiment_score": analysis.community_sentiment_score,
        "notable_shifts": analysis.notable_shifts or [],
        "summary": analysis.summary,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
    }
