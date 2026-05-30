"""Subreddit configuration API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.base import get_session
from src.database.models import Subreddit as SubredditModel
from src.features.configuration.schemas import (
    SubredditCreate,
    SubredditResponse,
    SubredditUpdate,
)

router = APIRouter()


@router.get("/", response_model=list[SubredditResponse])
async def list_subreddits(
    session: AsyncSession = Depends(get_session),
    include_inactive: bool = False,
) -> list[SubredditModel]:
    """List all configured subreddits."""
    query = select(SubredditModel)
    if not include_inactive:
        query = query.where(SubredditModel.is_active.is_(True))
    result = await session.execute(query.order_by(SubredditModel.name))
    return list(result.scalars().all())


@router.post("/", response_model=SubredditResponse, status_code=201)
async def create_subreddit(
    data: SubredditCreate,
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


@router.get("/{name}", response_model=SubredditResponse)
async def get_subreddit(
    name: str,
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


@router.patch("/{name}", response_model=SubredditResponse)
async def update_subreddit(
    name: str,
    data: SubredditUpdate,
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


@router.delete("/{name}", status_code=204)
async def delete_subreddit(
    name: str,
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
