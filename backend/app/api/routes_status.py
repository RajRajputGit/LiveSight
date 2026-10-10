"""Runtime status API router.

Conforms to Section 3 of 05_API_SPECIFICATION.md.
"""

from __future__ import annotations
from fastapi import APIRouter, Request
from backend.app.schemas.status import RuntimeStatusResponse

router = APIRouter(tags=["Status"])


@router.get(
    "/status",
    response_model=RuntimeStatusResponse,
    summary="Report pipeline runtime status",
    description="Reports the live state of the video source, model, tracking, and last frame timestamp.",
)
async def get_status(request: Request) -> RuntimeStatusResponse:
    """Return live pipeline and source telemetry status."""
    pipeline_service = getattr(request.app.state, "pipeline_service", None)
    if pipeline_service is not None:
        return pipeline_service.get_status()

    # Fallback status if pipeline service is not attached
    return RuntimeStatusResponse(
        pipeline_status="idle",
        source_id=None,
        source_type=None,
        model_loaded=False,
        tracking_enabled=False,
        last_frame_at=None,
        last_error=None,
    )
