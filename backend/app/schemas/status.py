"""Pydantic schemas for health and runtime status endpoints.

Conforms to Phase 4 specifications in 05_API_SPECIFICATION.md.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PipelineStatusEnum(str, Enum):
    """Enumerated state of the background vision pipeline."""

    RUNNING = "running"
    IDLE = "idle"
    STOPPED = "stopped"
    FAILED = "failed"


class HealthResponse(BaseModel):
    """Service health response matching GET /api/health specification."""

    status: str = Field("ok", description="Process health state")
    service: str = Field("ai-vision-backend", description="Service identifier")


class RuntimeStatusResponse(BaseModel):
    """Runtime status response matching GET /api/status specification."""

    pipeline_status: str = Field(
        ...,
        description="Status of the processing pipeline: running, idle, stopped, or failed",
    )
    source_id: Optional[str] = Field(None, description="Active camera/video source identifier")
    source_type: Optional[str] = Field(None, description="Source type: webcam, file, or unknown")
    model_loaded: bool = Field(False, description="Whether the YOLO model is loaded into memory")
    tracking_enabled: bool = Field(False, description="Whether ByteTrack tracking is active")
    last_frame_at: Optional[str] = Field(
        None, description="ISO-8601 UTC timestamp of the most recent processed frame"
    )
    last_error: Optional[str] = Field(
        None, description="Error message from the most recent failure, if any"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "pipeline_status": "running",
                "source_id": "local_camera_01",
                "source_type": "webcam",
                "model_loaded": True,
                "tracking_enabled": True,
                "last_frame_at": "2026-10-09T17:12:15.120Z",
                "last_error": None,
            }
        }
    }
