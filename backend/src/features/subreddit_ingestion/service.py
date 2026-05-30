"""Ingestion pipeline service."""
import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import AnalysisRun, Post, PostAnalysis, SubredditAnalysis
from src.database.models import Subreddit as SubredditModel
from src.features.post_analysis.llm_provider import LLMProvider
from src.features.post_analysis.schemas import PostPayload
from src.features.reddit_client.client import RedditClient
from src.shared.settings import get_settings

logger = logging.getLogger(__name__)


class IngestionService:
    """Orchestrates the Reddit ingestion and analysis pipeline."""

    def __init__(
        self,
        session: AsyncSession,
        reddit_client: RedditClient,
        llm_provider: LLMProvider,
        settings=None,
    ) -> None:
        self._session = session
        self._reddit = reddit_client
        self._llm = llm_provider
        self._settings = settings or get_settings()

    async def run_for_subreddit(self, subreddit_name: str) -> AnalysisRun:
        """Run a full ingestion and analysis cycle for a subreddit."""
        # Look up subreddit record
        result = await self._session.execute(
            select(SubredditModel).where(SubredditModel.name == subreddit_name)
        )
        subreddit = result.scalar_one_or_none()
        if subreddit is None:
            raise ValueError(f"Subreddit '{subreddit_name}' not found in database.")

        # Create run record
        run = AnalysisRun(subreddit_id=subreddit.id, status="running")
        self._session.add(run)
        await self._session.flush()

        try:
            post_summaries = await self._ingest_posts(subreddit, run)
            await self._run_meta_analysis(subreddit, run, post_summaries)

            run.status = "completed"
            run.completed_at = datetime.now(UTC)
            run.posts_processed = len(post_summaries)
        except Exception as exc:
            logger.exception("Ingestion failed for r/%s: %s", subreddit_name, exc)
            run.status = "failed"
            run.error_message = str(exc)
            run.completed_at = datetime.now(UTC)

        await self._session.flush()
        return run

    async def _ingest_posts(
        self, subreddit: SubredditModel, run: AnalysisRun
    ) -> list[str]:
        """Fetch, store, and analyze the hot posts for a subreddit."""
        feed = await self._reddit.get_hot_posts(
            subreddit.name, limit=self._settings.ingestion_top_posts
        )
        post_summaries: list[str] = []

        for reddit_post in feed.posts:
            # Upsert post record
            existing = await self._session.execute(
                select(Post).where(Post.reddit_id == reddit_post.reddit_id)
            )
            post = existing.scalar_one_or_none()
            if post is None:
                post = Post(
                    reddit_id=reddit_post.reddit_id,
                    subreddit_id=subreddit.id,
                    title=reddit_post.title,
                    body=reddit_post.body,
                    url=reddit_post.url,
                    score=reddit_post.score,
                    num_comments=reddit_post.num_comments,
                    author=reddit_post.author,
                    permalink=reddit_post.permalink,
                    reddit_created_at=reddit_post.created_utc,
                )
                self._session.add(post)
                await self._session.flush()
            else:
                post.score = reddit_post.score
                post.num_comments = reddit_post.num_comments
                await self._session.flush()

            # Fetch comments
            comments = await self._reddit.get_post_comments(
                reddit_post.permalink, limit=self._settings.ingestion_top_comments
            )
            comment_bodies = [c.body for c in comments]

            # LLM analysis
            try:
                payload = PostPayload(
                    post_title=reddit_post.title,
                    post_body=reddit_post.body,
                    top_comments=comment_bodies,
                )
                analysis_result = await self._llm.analyze_post(payload)

                # Upsert analysis
                existing_analysis = await self._session.execute(
                    select(PostAnalysis).where(PostAnalysis.post_id == post.id)
                )
                post_analysis = existing_analysis.scalar_one_or_none()
                if post_analysis is None:
                    post_analysis = PostAnalysis(post_id=post.id, analysis_run_id=run.id)
                    self._session.add(post_analysis)

                post_analysis.post_summary = analysis_result.post_summary
                post_analysis.overall_sentiment = analysis_result.overall_sentiment
                post_analysis.sentiment_score = analysis_result.sentiment_score
                post_analysis.key_community_takeaways = analysis_result.key_community_takeaways
                post_analysis.bullish_arguments = analysis_result.bullish_arguments
                post_analysis.bearish_arguments = analysis_result.bearish_arguments
                post_analysis.confidence = analysis_result.confidence
                post_analysis.top_comments_raw = comment_bodies
                post_analysis.analysis_run_id = run.id
                await self._session.flush()

                post_summaries.append(analysis_result.post_summary)
            except Exception as exc:
                logger.warning("Failed to analyze post %s: %s", reddit_post.reddit_id, exc)

        return post_summaries

    async def _run_meta_analysis(
        self,
        subreddit: SubredditModel,
        run: AnalysisRun,
        post_summaries: list[str],
    ) -> None:
        """Run a subreddit-level meta analysis across all post summaries."""
        if not post_summaries:
            logger.warning("No post summaries for r/%s; skipping meta analysis", subreddit.name)
            return

        today = datetime.now(UTC).strftime("%Y-%m-%d")
        try:
            result = await self._llm.analyze_subreddit(
                subreddit=subreddit.name,
                analysis_date=today,
                post_summaries=post_summaries,
            )

            meta = SubredditAnalysis(
                subreddit_id=subreddit.id,
                analysis_run_id=run.id,
                analysis_date=today,
                major_themes=result.major_themes,
                emerging_topics=result.emerging_topics,
                community_sentiment=result.community_sentiment,
                community_sentiment_score=result.community_sentiment_score,
                notable_shifts=result.notable_shifts,
                summary=result.summary,
            )
            self._session.add(meta)
            await self._session.flush()
        except Exception as exc:
            logger.exception("Meta analysis failed for r/%s: %s", subreddit.name, exc)
