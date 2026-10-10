"""Pydantic schemas for event models and API data contracts.

Conforms to Phase 4 specifications in 03_WORKFLOW_AND_DATA_CONTRACTS.md and 05_API_SPECIFICATION.md.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BoundingBoxDict(BaseModel):
    """Bounding box coordinates conforming to data contract {x1, y1, x2, y2}."""

    x1: float = Field(..., description="Top-left X coordinate")
    y1: float = Field(..., description="Top-left Y coordinate")
    x2: float = Field(..., description="Bottom-right X coordinate")
    y2: float = Field(..., description="Bottom-right Y coordinate")


class EventResponse(BaseModel):
    """Individual domain event contract matching documented REST/WebSocket format."""

    event_id: str = Field(..., description="Unique event identifier (e.g. evt_01J...)")
    camera_id: str = Field(..., description="Stable source or camera identifier")
    event_type: str = Field(..., description="Machine-readable event name (e.g. restricted_zone_intrusion)")
    occurred_at: str = Field(..., description="UTC ISO-8601 timestamp with timezone")
    object_class: str = Field(..., description="Detected object class (e.g. person)")
    track_id: Optional[str] = Field(None, description="Tracker session identifier, if available")
    confidence: float = Field(..., description="Model detection confidence score")
    zone_id: str = Field(..., description="Restricted zone identifier")
    bbox: Optional[BoundingBoxDict] = Field(None, description="Event-time bounding box")
    snapshot_path: Optional[str] = Field(None, description="Optional path to saved snapshot asset")

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_id": "evt_01JEXAMPLE",
                "camera_id": "local_camera_01",
                "event_type": "restricted_zone_intrusion",
                "occurred_at": "2026-10-09T17:12:15.120Z",
                "object_class": "person",
                "track_id": "7",
                "confidence": 0.94,
                "zone_id": "restricted_zone_A",
                "bbox": {"x1": 120.0, "y1": 80.0, "x2": 260.0, "y2": 430.0},
                "snapshot_path": None,
            }
        }
    }


class EventListResponse(BaseModel):
    """Paginated list of historical events."""

    items: List[EventResponse] = Field(default_factory=list, description="List of domain events")
    next_cursor: Optional[str] = Field(None, description="Pagination cursor for retrieving the next page")


class EventStreamMessage(BaseModel):
    """WebSocket broadcast message wrapper."""

    type: str = Field("event.created", description="Message event type")
    data: EventResponse = Field(..., description="Domain event payload")
