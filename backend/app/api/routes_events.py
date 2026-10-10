"""Event history REST API router.

Conforms to Section 4 and Section 6 of 05_API_SPECIFICATION.md.
"""

from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from backend.app.schemas.error import ErrorDetail, ErrorResponse
from backend.app.schemas.event import EventListResponse

router = APIRouter(tags=["Events"])


@router.get(
    "/events",
    response_model=EventListResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid query parameters"},
        500: {"model": ErrorResponse, "description": "Database query failure"},
    },
    summary="Query historical domain events",
    description="Returns paginated domain events ordered by occurred_at DESC.",
)
async def get_events(
    request: Request,
    limit: Optional[int] = Query(
        50,
        description="Maximum items to return (1 to 100)",
    ),
    before: Optional[str] = Query(
        None,
        description="Optional ISO-8601 timestamp cursor for pagination",
    ),
    event_type: Optional[str] = Query(
        None,
        description="Filter events by event_type (e.g. restricted_zone_intrusion)",
    ),
    camera_id: Optional[str] = Query(
        None,
        description="Filter events by camera or source identifier",
    ),
) -> EventListResponse:
    """Retrieve historical events matching optional filter and cursor criteria."""
    # Explicit validation for limit
    if limit is None or limit < 1 or limit > 100:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_QUERY",
                    "message": "The limit parameter must be between 1 and 100.",
                }
            },
        )

    event_service = getattr(request.app.state, "event_service", None)
    if event_service is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Event service is unavailable.",
                }
            },
        )

    try:
        return event_service.get_events(
            limit=limit,
            before=before,
            event_type=event_type,
            camera_id=camera_id,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "DATABASE_ERROR",
                    "message": f"Failed to retrieve events: {exc}",
                }
            },
        )
