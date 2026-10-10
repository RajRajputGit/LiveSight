"""API routers export."""

from backend.app.api.routes_events import router as events_router
from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_status import router as status_router
from backend.app.api.routes_stream import router as stream_router

__all__ = ["health_router", "status_router", "events_router", "stream_router"]
