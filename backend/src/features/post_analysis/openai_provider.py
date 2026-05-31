"""OpenAI LLM provider implementation."""
import logging

from openai import AsyncOpenAI

from src.features.post_analysis.llm_provider import LLMProvider
from src.shared.settings import get_settings

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI-backed LLM provider."""

    def __init__(self, settings=None) -> None:
        self._settings = settings or get_settings()
        self._client = AsyncOpenAI(api_key=self._settings.openai_api_key)

    def _build_completion_params(self, system_prompt: str, user_content: str) -> dict:
        """Build chat completion parameters compatible with the configured model."""
        params = {
            "model": self._settings.openai_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        if not self._settings.openai_model.startswith("gpt-5"):
            params["temperature"] = self._settings.openai_temperature
        return params

    async def complete(self, system_prompt: str, user_content: str) -> str:
        """Generate a completion using the OpenAI chat completions API."""
        response = await self._client.chat.completions.create(
            **self._build_completion_params(system_prompt, user_content)
        )
        return response.choices[0].message.content or ""


def get_llm_provider(settings=None) -> LLMProvider:
    """Factory function to get the configured LLM provider."""
    return OpenAIProvider(settings=settings)
