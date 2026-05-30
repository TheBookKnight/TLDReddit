"""LLM provider abstraction layer."""
import json
import logging
from abc import ABC, abstractmethod

from pydantic import ValidationError

from src.features.post_analysis.schemas import (
    PostAnalysisResult,
    PostPayload,
    SubredditAnalysisResult,
)

logger = logging.getLogger(__name__)

POST_ANALYSIS_SYSTEM = """You are an expert at analyzing Reddit discussions.
Given a Reddit post and its top comments, produce a structured JSON analysis.

Respond ONLY with valid JSON matching this exact schema:
{
  "post_summary": "string - concise 2-3 sentence summary",
  "overall_sentiment": "one of: positive, negative, neutral, mixed",
  "sentiment_score": float between -1.0 and 1.0,
  "key_community_takeaways": ["list of key points from the community"],
  "bullish_arguments": ["optimistic/positive arguments made"],
  "bearish_arguments": ["pessimistic/negative arguments made"],
  "confidence": float between 0.0 and 1.0
}"""

SUBREDDIT_ANALYSIS_SYSTEM = """You are an expert at analyzing Reddit community trends.
Given summaries of the top posts from a subreddit, produce a structured JSON meta-analysis.

Respond ONLY with valid JSON matching this exact schema:
{
  "subreddit": "string",
  "analysis_date": "YYYY-MM-DD",
  "major_themes": ["list of major recurring themes"],
  "emerging_topics": ["list of new or growing topics"],
  "community_sentiment": "one of: positive, negative, neutral, mixed",
  "community_sentiment_score": float between -1.0 and 1.0,
  "notable_shifts": ["notable changes or shifts in discussion"],
  "summary": "string - 3-5 sentence overview of the subreddit state"
}"""


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    @abstractmethod
    async def complete(self, system_prompt: str, user_content: str) -> str:
        """Generate a completion from the LLM."""

    async def analyze_post(self, payload: PostPayload) -> PostAnalysisResult:
        """Analyze a Reddit post and return structured results."""
        user_content = (
            f"Post Title: {payload.post_title}\n\n"
            f"Post Body: {payload.post_body or '(no body)'}\n\n"
            f"Top Comments:\n"
            + "\n---\n".join(payload.top_comments[:20])
        )

        raw = await self.complete(POST_ANALYSIS_SYSTEM, user_content)
        return self._parse_post_analysis(raw)

    async def analyze_subreddit(
        self, subreddit: str, analysis_date: str, post_summaries: list[str]
    ) -> SubredditAnalysisResult:
        """Run a meta-analysis across all post summaries for a subreddit."""
        user_content = (
            f"Subreddit: r/{subreddit}\n"
            f"Date: {analysis_date}\n\n"
            f"Post Summaries:\n"
            + "\n\n---\n\n".join(post_summaries)
        )

        raw = await self.complete(SUBREDDIT_ANALYSIS_SYSTEM, user_content)
        return self._parse_subreddit_analysis(raw, subreddit, analysis_date)

    def _parse_post_analysis(self, raw: str) -> PostAnalysisResult:
        """Parse and validate the raw LLM post analysis response."""
        try:
            data = json.loads(raw)
            return PostAnalysisResult(**data)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.error("Failed to parse post analysis: %s\nRaw: %s", exc, raw[:500])
            raise ValueError(f"Malformed LLM post analysis output: {exc}") from exc

    def _parse_subreddit_analysis(
        self, raw: str, subreddit: str, analysis_date: str
    ) -> SubredditAnalysisResult:
        """Parse and validate the raw LLM subreddit analysis response."""
        try:
            data = json.loads(raw)
            # Ensure subreddit/date are set correctly
            data["subreddit"] = subreddit
            data["analysis_date"] = analysis_date
            return SubredditAnalysisResult(**data)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.error("Failed to parse subreddit analysis: %s\nRaw: %s", exc, raw[:500])
            raise ValueError(f"Malformed LLM subreddit analysis output: {exc}") from exc
