"""Application settings and configuration."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./tldreddit.db")

    # OpenAI
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o-mini")
    openai_temperature: float = Field(default=0.2)

    # Reddit
    reddit_user_agent: str = Field(default="TLDReddit/1.0 (by /u/tldreddit_bot)")
    reddit_request_delay: float = Field(default=1.0)
    reddit_max_retries: int = Field(default=3)

    # Ingestion
    ingestion_top_posts: int = Field(default=10)
    ingestion_top_comments: int = Field(default=20)
    ingestion_schedule_hour: int = Field(default=6)
    ingestion_schedule_minute: int = Field(default=0)

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:5173", "http://localhost:3000"])

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
