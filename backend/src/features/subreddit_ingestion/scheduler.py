"""APScheduler-based daily ingestion scheduler."""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.shared.settings import get_settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _daily_ingestion_job() -> None:
    """Daily scheduled job that runs ingestion for all active subreddits."""
    from sqlalchemy import select

    from src.database.base import get_session_factory
    from src.database.models import Subreddit as SubredditModel
    from src.features.post_analysis.openai_provider import get_llm_provider
    from src.features.reddit_client.client import RedditClient
    from src.features.subreddit_ingestion.service import IngestionService

    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(
            select(SubredditModel).where(SubredditModel.is_active.is_(True))
        )
        subreddits = result.scalars().all()

    for subreddit in subreddits:
        try:
            async with session_factory() as session:
                async with RedditClient() as reddit:
                    llm = get_llm_provider()
                    svc = IngestionService(session, reddit, llm)
                    await svc.run_for_subreddit(subreddit.name)
                    await session.commit()
            logger.info("Daily ingestion completed for r/%s", subreddit.name)
        except Exception as exc:
            logger.exception("Daily ingestion failed for r/%s: %s", subreddit.name, exc)


def start_scheduler() -> AsyncIOScheduler:
    """Create and start the APScheduler scheduler."""
    global _scheduler
    settings = get_settings()

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        _daily_ingestion_job,
        "cron",
        hour=settings.ingestion_schedule_hour,
        minute=settings.ingestion_schedule_minute,
        id="daily_ingestion",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "Scheduler started: daily ingestion at %02d:%02d UTC",
        settings.ingestion_schedule_hour,
        settings.ingestion_schedule_minute,
    )
    return _scheduler


def stop_scheduler() -> None:
    """Stop the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
        _scheduler = None
        logger.info("Scheduler stopped")
