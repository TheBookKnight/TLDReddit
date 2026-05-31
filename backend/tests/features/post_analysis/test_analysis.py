"""Tests for LLM analysis schemas and provider."""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from src.features.post_analysis.llm_provider import LLMProvider
from src.features.post_analysis.openai_provider import OpenAIProvider
from src.features.post_analysis.schemas import (
    PostAnalysisResult,
    PostPayload,
    SubredditAnalysisResult,
)
from src.shared.settings import Settings


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, response: str) -> None:
        self._response = response

    async def complete(self, system_prompt: str, user_content: str) -> str:
        return self._response


VALID_POST_ANALYSIS = {
    "post_summary": "This is a test summary of the Reddit post.",
    "overall_sentiment": "positive",
    "sentiment_score": 0.75,
    "key_community_takeaways": ["Takeaway 1", "Takeaway 2"],
    "bullish_arguments": ["Bullish point 1"],
    "bearish_arguments": ["Bearish point 1"],
    "confidence": 0.85,
}

VALID_SUBREDDIT_ANALYSIS = {
    "subreddit": "test",
    "analysis_date": "2024-01-01",
    "major_themes": ["Theme 1", "Theme 2"],
    "emerging_topics": ["Topic 1"],
    "community_sentiment": "neutral",
    "community_sentiment_score": 0.1,
    "notable_shifts": ["Shift 1"],
    "summary": "This subreddit is discussing various topics.",
}


def test_post_analysis_result_valid():
    """Test valid PostAnalysisResult creation."""
    result = PostAnalysisResult(**VALID_POST_ANALYSIS)
    assert result.post_summary == VALID_POST_ANALYSIS["post_summary"]
    assert result.overall_sentiment == "positive"
    assert result.sentiment_score == 0.75


def test_post_analysis_result_sentiment_case_insensitive():
    """Test that sentiment validation is case-insensitive."""
    data = {**VALID_POST_ANALYSIS, "overall_sentiment": "POSITIVE"}
    result = PostAnalysisResult(**data)
    assert result.overall_sentiment == "positive"


def test_post_analysis_result_invalid_sentiment():
    """Test that invalid sentiment raises ValueError."""
    from pydantic import ValidationError

    data = {**VALID_POST_ANALYSIS, "overall_sentiment": "bullish"}
    with pytest.raises(ValidationError):
        PostAnalysisResult(**data)


def test_post_analysis_result_sentiment_score_bounds():
    """Test that sentiment score out of bounds raises ValidationError."""
    from pydantic import ValidationError

    data = {**VALID_POST_ANALYSIS, "sentiment_score": 1.5}
    with pytest.raises(ValidationError):
        PostAnalysisResult(**data)

    data = {**VALID_POST_ANALYSIS, "sentiment_score": -1.5}
    with pytest.raises(ValidationError):
        PostAnalysisResult(**data)


def test_subreddit_analysis_result_valid():
    """Test valid SubredditAnalysisResult creation."""
    result = SubredditAnalysisResult(**VALID_SUBREDDIT_ANALYSIS)
    assert result.subreddit == "test"
    assert result.community_sentiment == "neutral"


def test_subreddit_analysis_result_invalid_sentiment():
    """Test that invalid community sentiment raises ValidationError."""
    from pydantic import ValidationError

    data = {**VALID_SUBREDDIT_ANALYSIS, "community_sentiment": "excellent"}
    with pytest.raises(ValidationError):
        SubredditAnalysisResult(**data)


@pytest.mark.asyncio
async def test_llm_provider_analyze_post_success():
    """Test successful post analysis via LLM provider."""
    provider = MockLLMProvider(json.dumps(VALID_POST_ANALYSIS))
    payload = PostPayload(
        post_title="Test title",
        post_body="Test body",
        top_comments=["Comment 1", "Comment 2"],
    )
    result = await provider.analyze_post(payload)
    assert isinstance(result, PostAnalysisResult)
    assert result.sentiment_score == 0.75


@pytest.mark.asyncio
async def test_llm_provider_analyze_post_malformed_json():
    """Test that malformed JSON raises ValueError."""
    provider = MockLLMProvider("not valid json")
    payload = PostPayload(post_title="Test")

    with pytest.raises(ValueError, match="Malformed LLM"):
        await provider.analyze_post(payload)


@pytest.mark.asyncio
async def test_llm_provider_analyze_subreddit_success():
    """Test successful subreddit meta-analysis."""
    provider = MockLLMProvider(json.dumps(VALID_SUBREDDIT_ANALYSIS))
    result = await provider.analyze_subreddit(
        subreddit="test",
        analysis_date="2024-01-01",
        post_summaries=["Summary 1", "Summary 2"],
    )
    assert isinstance(result, SubredditAnalysisResult)
    assert result.subreddit == "test"


@pytest.mark.asyncio
async def test_llm_provider_analyze_subreddit_sets_correct_subreddit():
    """Test that analyze_subreddit always uses the provided subreddit name."""
    data = {**VALID_SUBREDDIT_ANALYSIS, "subreddit": "wrong_subreddit"}
    provider = MockLLMProvider(json.dumps(data))
    result = await provider.analyze_subreddit(
        subreddit="correctsubreddit",
        analysis_date="2024-01-01",
        post_summaries=["Summary"],
    )
    assert result.subreddit == "correctsubreddit"


@pytest.mark.asyncio
async def test_llm_provider_limits_comments():
    """Test that only the first 20 comments are sent to the LLM."""
    responses = []

    async def capture_complete(self, system: str, user_content: str) -> str:
        responses.append(user_content)
        return json.dumps(VALID_POST_ANALYSIS)

    provider = MockLLMProvider(json.dumps(VALID_POST_ANALYSIS))
    provider.complete = lambda s, u: capture_complete(provider, s, u)  # type: ignore

    comments = [f"Comment {i}" for i in range(25)]
    payload = PostPayload(
        post_title="Test",
        top_comments=comments,
    )

    # This should work without error even with many comments
    result = await provider.analyze_post(payload)
    assert isinstance(result, PostAnalysisResult)


@pytest.mark.asyncio
async def test_openai_provider_omits_temperature_for_gpt5_models():
    """Test GPT-5 models do not receive an explicit temperature parameter."""
    provider = OpenAIProvider(
        settings=Settings(
            openai_api_key="test",
            openai_model="gpt-5-mini",
            openai_temperature=0.2,
            database_url="sqlite+aiosqlite:///:memory:",
        )
    )
    create_mock = AsyncMock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))]
        )
    )
    provider._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create_mock))
    )

    result = await provider.complete("system", "user")

    assert result == '{"ok": true}'
    kwargs = create_mock.await_args.kwargs
    assert kwargs["model"] == "gpt-5-mini"
    assert "temperature" not in kwargs


@pytest.mark.asyncio
async def test_openai_provider_keeps_temperature_for_non_gpt5_models():
    """Test legacy models continue receiving the configured temperature."""
    provider = OpenAIProvider(
        settings=Settings(
            openai_api_key="test",
            openai_model="gpt-4o-mini",
            openai_temperature=0.2,
            database_url="sqlite+aiosqlite:///:memory:",
        )
    )
    create_mock = AsyncMock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))]
        )
    )
    provider._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create_mock))
    )

    await provider.complete("system", "user")

    kwargs = create_mock.await_args.kwargs
    assert kwargs["temperature"] == 0.2
