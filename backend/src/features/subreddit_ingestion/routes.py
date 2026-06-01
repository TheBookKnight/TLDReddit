"""Ingestion API routes."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.base import get_session
from src.database.models import AnalysisRun
from src.database.models import Subreddit as SubredditModel
from src.features.post_analysis.openai_provider import get_llm_provider
from src.features.reddit_client.client import RedditClient
from src.features.subreddit_ingestion.schemas import (
    AnalysisRunResponse,
    IngestionTriggerAllResponse,
    IngestionTriggerResponse,
)
from src.features.subreddit_ingestion.service import IngestionService

router = APIRouter()


async def _run_ingestion(subreddit_name: str) -> None:
    """Background task runner for a single subreddit ingestion."""
    from src.database.base import get_session_factory

    session_factory = get_session_factory()
    async with session_factory() as session:
        async with RedditClient() as reddit:
            llm = get_llm_provider()
            svc = IngestionService(session, reddit, llm)
            await svc.run_for_subreddit(subreddit_name)
            await session.commit()


@router.post(
    "/run/{subreddit_name}",
    response_model=IngestionTriggerResponse,
    status_code=202,
    summary="Trigger subreddit ingestion",
    description="Queue a background ingestion and analysis run for a single monitored subreddit.",
)
async def trigger_ingestion(
    background_tasks: BackgroundTasks,
    subreddit_name: str = Path(
        ...,
        description="Canonical subreddit name without the r/ prefix.",
        examples=["stocks"],
    ),
    session: AsyncSession = Depends(get_session),
) -> IngestionTriggerResponse:
    """Trigger an ingestion run for a specific subreddit."""
    result = await session.execute(
        select(SubredditModel).where(SubredditModel.name == subreddit_name)
    )
    subreddit = result.scalar_one_or_none()
    if subreddit is None:
        raise HTTPException(status_code=404, detail=f"Subreddit '{subreddit_name}' not found.")

    background_tasks.add_task(_run_ingestion, subreddit_name)
    return IngestionTriggerResponse(
        message=f"Ingestion started for r/{subreddit_name}",
        subreddit=subreddit_name,
    )


@router.post(
    "/run-all",
    response_model=IngestionTriggerAllResponse,
    status_code=202,
    summary="Trigger ingestion for all active subreddits",
    description=(
        "Queue background ingestion and analysis runs for every active "
        "monitored subreddit."
    ),
)
async def trigger_all_ingestion(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> IngestionTriggerAllResponse:
    """Trigger ingestion for all active subreddits."""
    result = await session.execute(
        select(SubredditModel).where(SubredditModel.is_active.is_(True))
    )
    subreddits = result.scalars().all()

    for subreddit in subreddits:
        background_tasks.add_task(_run_ingestion, subreddit.name)

    return IngestionTriggerAllResponse(
        message=f"Ingestion started for {len(subreddits)} subreddits",
        subreddits=[s.name for s in subreddits],
    )


@router.get(
    "/runs/{subreddit_name}",
    response_model=list[AnalysisRunResponse],
    summary="List ingestion runs",
    description="Return recent ingestion and analysis runs recorded for a monitored subreddit.",
)
async def list_runs(
    subreddit_name: str = Path(
        ...,
        description="Canonical subreddit name without the r/ prefix.",
        examples=["stocks"],
    ),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of recent runs to return.",
    ),
) -> list[AnalysisRunResponse]:
    """List recent analysis runs for a subreddit."""
    result = await session.execute(
        select(SubredditModel).where(SubredditModel.name == subreddit_name)
    )
    subreddit = result.scalar_one_or_none()
    if subreddit is None:
        raise HTTPException(status_code=404, detail=f"Subreddit '{subreddit_name}' not found.")

    runs_result = await session.execute(
        select(AnalysisRun)
        .where(AnalysisRun.subreddit_id == subreddit.id)
        .order_by(AnalysisRun.started_at.desc())
        .limit(limit)
    )
    runs = runs_result.scalars().all()

    return [
        AnalysisRunResponse(
            id=r.id,
            status=r.status,
            posts_processed=r.posts_processed,
            started_at=r.started_at.isoformat() if r.started_at else None,
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
            error_message=r.error_message,
        )
        for r in runs
    ]
