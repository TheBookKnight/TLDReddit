"""TLDReddit Backend Application."""
import contextlib
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database.base import init_db
from src.features.chatbot.routes import router as chat_router
from src.features.configuration.routes import router as config_router
from src.features.dashboard.routes import router as dashboard_router
from src.features.subreddit_ingestion.routes import router as ingestion_router
from src.features.trend_analysis.routes import router as trends_router
from src.shared.settings import get_settings


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    await init_db()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="TLDReddit API",
        description="Reddit Trend Intelligence Platform API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(config_router, prefix="/api/v1/subreddits", tags=["subreddits"])
    app.include_router(ingestion_router, prefix="/api/v1/ingestion", tags=["ingestion"])
    app.include_router(trends_router, prefix="/api/v1/trends", tags=["trends"])
    app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])
    app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])

    @app.get("/api/v1/health")
    async def health_check() -> dict:
        return {"status": "healthy", "version": "1.0.0"}

    return app


app = create_app()
