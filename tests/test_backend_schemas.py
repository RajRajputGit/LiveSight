"""Unit tests for Phase 4 Pydantic backend schemas."""

import pytest
from pydantic import ValidationError

from backend.app.schemas.error import ErrorDetail, ErrorResponse
from backend.app.schemas.event import (
    BoundingBoxDict,
    EventListResponse,
    EventResponse,
    EventStreamMessage,
)
from backend.app.schemas.status import (
    HealthResponse,
    PipelineStatusEnum,
    RuntimeStatusResponse,
)


def test_bounding_box_dict():
    bbox = BoundingBoxDict(x1=10.0, y1=20.0, x2=50.0, y2=80.0)
    assert bbox.x1 == 10.0
    assert bbox.y1 == 20.0
    assert bbox.x2 == 50.0
    assert bbox.y2 == 80.0


def test_event_response_valid():
    event = EventResponse(
        event_id="evt_01JTEST",
        camera_id="cam_01",
        event_type="restricted_zone_intrusion",
        occurred_at="2026-10-10T12:00:00.000Z",
        object_class="person",
        track_id="42",
        confidence=0.88,
        zone_id="zone_A",
        bbox=BoundingBoxDict(x1=10, y1=20, x2=30, y2=40),
        snapshot_path=None,
    )
    assert event.event_id == "evt_01JTEST"
    assert event.track_id == "42"
    assert event.bbox.x1 == 10.0


def test_event_response_missing_required():
    with pytest.raises(ValidationError):
        EventResponse(
            event_id="evt_01",
            camera_id="cam_01",
            # missing event_type, occurred_at, object_class, confidence, zone_id
        )


def test_event_list_response():
    list_resp = EventListResponse(items=[], next_cursor="2026-10-10T11:00:00.000Z")
    assert len(list_resp.items) == 0
    assert list_resp.next_cursor == "2026-10-10T11:00:00.000Z"


def test_event_stream_message():
    event = EventResponse(
        event_id="evt_ws",
        camera_id="cam_01",
        event_type="restricted_zone_intrusion",
        occurred_at="2026-10-10T12:00:00.000Z",
        object_class="person",
        confidence=0.9,
        zone_id="zone_A",
    )
    msg = EventStreamMessage(type="event.created", data=event)
    assert msg.type == "event.created"
    assert msg.data.event_id == "evt_ws"


def test_health_response():
    h = HealthResponse()
    assert h.status == "ok"
    assert h.service == "ai-vision-backend"


def test_runtime_status_response():
    status = RuntimeStatusResponse(
        pipeline_status=PipelineStatusEnum.RUNNING.value,
        source_id="local_camera_01",
        source_type="webcam",
        model_loaded=True,
        tracking_enabled=True,
        last_frame_at="2026-10-10T12:00:00.000Z",
        last_error=None,
    )
    assert status.pipeline_status == "running"
    assert status.model_loaded is True
    assert status.source_type == "webcam"


def test_error_response_shape():
    err = ErrorResponse(
        error=ErrorDetail(code="INVALID_QUERY", message="Limit is out of range.")
    )
    d = err.model_dump()
    assert d == {
        "error": {
            "code": "INVALID_QUERY",
            "message": "Limit is out of range.",
        }
    }
