"""FastAPI entry point for LiveSight Backend Application.

Conforms to Phase 4 specifications in 02_SYSTEM_ARCHITECTURE.md,
04_IMPLEMENTATION_PLAN.md, and 05_API_SPECIFICATION.md:
- Health endpoint: GET /api/health
- Runtime status endpoint: GET /api/status
- Event history endpoint: GET /api/events (with pagination & filtering)
- Live WebSocket stream: WS /api/events/stream
- Decoupled background pipeline service
- SQLite repository persistence
- Standardized error format
"""

from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.api import events_router, health_router, status_router, stream_router
from backend.app.config import Settings, settings
from backend.app.repositories.event_repository import EventRepository
from backend.app.services.event_publisher import EventPublisher
from backend.app.services.event_service import EventService
from backend.app.services.pipeline_service import PipelineService

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("livesight.backend")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing background services, repository, and connections."""
    app_settings: Settings = getattr(app.state, "settings", settings)
    loop = asyncio.get_running_loop()

    # 1. Initialize SQLite repository
    db_path = app_settings.get_absolute_database_path()
    repository = EventRepository(database_path=db_path)

    # 2. Initialize publisher and event service
    publisher = EventPublisher()
    publisher.set_event_loop(loop)
    event_service = EventService(repository=repository, publisher=publisher)

    # 3. Initialize background pipeline service
    pipeline_service = PipelineService(event_service=event_service)

    # Attach to application state
    app.state.repository = repository
    app.state.event_publisher = publisher
    app.state.event_service = event_service
    app.state.pipeline_service = pipeline_service

    logger.info("LiveSight backend services initialized. DB: %s", db_path)

    # 4. Optionally launch background vision worker if configured
    if app_settings.start_pipeline_on_startup:
        logger.info("Auto-starting background vision worker on startup...")
        pipeline_service.start(
            source_target=app_settings.video_source or 0,
            model_name=app_settings.model_name,
            confidence=app_settings.confidence_threshold,
            enable_tracking=app_settings.tracking_enabled,
            tracker_config=app_settings.tracker_config,
            rules_config=app_settings.rules_config,
        )

    yield

    # Teardown
    logger.info("Shutting down LiveSight backend services...")
    if pipeline_service is not None:
        pipeline_service.stop(timeout=3.0)
    logger.info("LiveSight backend shutdown complete.")


def create_app(custom_settings: Settings = settings) -> FastAPI:
    """Factory creating configured FastAPI instance."""
    app = FastAPI(
        title="LiveSight API",
        description="Real-Time AI Vision, Multi-Object Tracking & Event Engine Backend",
        version="0.4.0",
        lifespan=lifespan,
    )

    app.state.settings = custom_settings

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=custom_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Standardized validation error handler (Section 6 of 05_API_SPECIFICATION.md)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        first_error = exc.errors()[0] if exc.errors() else {"msg": "Invalid query parameters"}
        msg = first_error.get("msg", "Invalid parameter value.")
        loc = first_error.get("loc", ["query"])
        field = loc[-1] if loc else "parameter"
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_QUERY",
                    "message": f"Invalid {field}: {msg}",
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": str(exc.detail),
                }
            },
        )

    # Register routers under /api prefix
    app.include_router(health_router, prefix="/api")
    app.include_router(status_router, prefix="/api")
    app.include_router(events_router, prefix="/api")
    app.include_router(stream_router, prefix="/api")

    return app


app = create_app()
