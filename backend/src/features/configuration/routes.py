"""Subreddit configuration API routes."""
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.base import get_session
from src.database.models import AnalysisRun, Post, PostAnalysis, SubredditAnalysis
from src.database.models import Subreddit as SubredditModel
from src.features.configuration.schemas import (
    SubredditCreate,
    SubredditResponse,
    SubredditUpdate,
)

router = APIRouter()


@router.get(
    "/",
    response_model=list[SubredditResponse],
    summary="List configured subreddits",
    description=(
        "Return the monitored subreddit configurations, optionally "
        "including inactive entries."
    ),
)
async def list_subreddits(
    session: AsyncSession = Depends(get_session),
    include_inactive: bool = Query(
        default=False,
        description="Include subreddits that have been disabled for monitoring.",
    ),
) -> list[SubredditModel]:
    """List all configured subreddits."""
    query = select(SubredditModel)
    if not include_inactive:
        query = query.where(SubredditModel.is_active.is_(True))
    result = await session.execute(query.order_by(SubredditModel.name))
    return list(result.scalars().all())


@router.post(
    "/",
    response_model=SubredditResponse,
    status_code=201,
    summary="Create a subreddit configuration",
    description=(
        "Add a subreddit to the monitoring list so ingestion and "
        "downstream analysis can process it."
    ),
)
async def create_subreddit(
    data: SubredditCreate = Body(
        ...,
        description="Configuration values for the subreddit to monitor.",
    ),
    session: AsyncSession = Depends(get_session),
) -> SubredditModel:
    """Add a new subreddit to monitor."""
    existing = await session.execute(
        select(SubredditModel).where(SubredditModel.name == data.name)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail=f"Subreddit '{data.name}' already exists.")

    subreddit = SubredditModel(
        name=data.name,
        display_name=data.display_name,
        description=data.description,
    )
    session.add(subreddit)
    await session.flush()
    await session.refresh(subreddit)
    return subreddit

# WARNING: The following route deletes all subreddits and related data.
# Use with caution and ensure proper authentication/authorization is in
# place in a production environment.
@router.delete(
    "/",
    summary="Delete all subreddit data",
    description=(
        "Permanently remove all configured subreddits together with "
        "their stored posts, analyses, and ingestion runs."
    ),
)
async def delete_all_subreddits(
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    """Delete all subreddit configuration and related analysis data."""
    result = await session.execute(select(SubredditModel.id))
    subreddit_ids = list(result.scalars().all())
    if not subreddit_ids:
        return {"deleted_subreddits": 0}

    await session.execute(
        delete(PostAnalysis).where(
            PostAnalysis.post_id.in_(select(Post.id).where(Post.subreddit_id.in_(subreddit_ids)))
        )
    )
    await session.execute(
        delete(SubredditAnalysis).where(SubredditAnalysis.subreddit_id.in_(subreddit_ids))
    )
    await session.execute(
        delete(AnalysisRun).where(AnalysisRun.subreddit_id.in_(subreddit_ids))
    )
    await session.execute(
        delete(Post).where(Post.subreddit_id.in_(subreddit_ids))
    )
    await session.execute(
        delete(SubredditModel).where(SubredditModel.id.in_(subreddit_ids))
    )
    await session.flush()

    return {"deleted_subreddits": len(subreddit_ids)}


@router.get(
    "/{name}",
    response_model=SubredditResponse,
    summary="Get subreddit configuration",
    description="Fetch the stored configuration for a single subreddit by name.",
)
async def get_subreddit(
    name: str = Path(
        ...,
        description="Canonical subreddit name without the r/ prefix.",
        examples=["stocks"],
    ),
    session: AsyncSession = Depends(get_session),
) -> SubredditModel:
    """Get a specific subreddit by name."""
    result = await session.execute(
        select(SubredditModel).where(SubredditModel.name == name)
    )
    subreddit = result.scalar_one_or_none()
    if subreddit is None:
        raise HTTPException(status_code=404, detail=f"Subreddit '{name}' not found.")
    return subreddit


@router.patch(
    "/{name}",
    response_model=SubredditResponse,
    summary="Update subreddit configuration",
    description="Modify display metadata or activation status for an existing monitored subreddit.",
)
async def update_subreddit(
    name: str = Path(
        ...,
        description="Canonical subreddit name without the r/ prefix.",
        examples=["stocks"],
    ),
    data: SubredditUpdate = Body(
        ...,
        description="Subset of subreddit fields to update.",
    ),
    session: AsyncSession = Depends(get_session),
) -> SubredditModel:
    """Update a subreddit configuration."""
    result = await session.execute(
        select(SubredditModel).where(SubredditModel.name == name)
    )
    subreddit = result.scalar_one_or_none()
    if subreddit is None:
        raise HTTPException(status_code=404, detail=f"Subreddit '{name}' not found.")

    if data.display_name is not None:
        subreddit.display_name = data.display_name
    if data.description is not None:
        subreddit.description = data.description
    if data.is_active is not None:
        subreddit.is_active = data.is_active

    await session.flush()
    await session.refresh(subreddit)
    return subreddit


@router.delete(
    "/{name}",
    status_code=204,
    summary="Disable subreddit monitoring",
    description=(
        "Soft-delete a subreddit by marking it inactive so new ingestion "
        "stops without removing history."
    ),
)
async def delete_subreddit(
    name: str = Path(
        ...,
        description="Canonical subreddit name without the r/ prefix.",
        examples=["stocks"],
    ),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Remove a subreddit from monitoring (soft delete via is_active=False)."""
    result = await session.execute(
        select(SubredditModel).where(SubredditModel.name == name)
    )
    subreddit = result.scalar_one_or_none()
    if subreddit is None:
        raise HTTPException(status_code=404, detail=f"Subreddit '{name}' not found.")

    subreddit.is_active = False
    await session.flush()
