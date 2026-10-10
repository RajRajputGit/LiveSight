"""Health check API router.

Conforms to Section 2 of 05_API_SPECIFICATION.md.
"""

from __future__ import annotations
from fastapi import APIRouter
from backend.app.schemas.status import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Report process health",
    description="Reports whether the backend process is healthy and responding.",
)
async def get_health() -> HealthResponse:
    """Return static process status response."""
    return HealthResponse(status="ok", service="ai-vision-backend")
