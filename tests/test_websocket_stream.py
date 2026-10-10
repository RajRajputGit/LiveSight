"""Integration tests for live WebSocket event stream (WS /api/events/stream).

Conforms to Section 5 and Section 8 of 05_API_SPECIFICATION.md.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app
from rules.schemas import DomainEvent


@pytest.fixture
def app_and_client(tmp_path: Path):
    """Fixture providing configured app and TestClient."""
    db_file = tmp_path / "ws_test.db"

    test_settings = Settings()
    test_settings.database_path = str(db_file)
    test_settings.start_pipeline_on_startup = False

    app = create_app(custom_settings=test_settings)
    with TestClient(app) as client:
        yield app, client


def test_websocket_stream_receives_broadcast(app_and_client):
    app, client = app_and_client
    event_service = app.state.event_service

    with client.websocket_connect("/api/events/stream") as websocket:
        # Create and record an event via EventService
        event = DomainEvent.create(
            camera_id="cam_ws_01",
            event_type="restricted_zone_intrusion",
            object_class="person",
            zone_id="restricted_zone_A",
            confidence=0.91,
            bbox={"x1": 120.0, "y1": 80.0, "x2": 260.0, "y2": 430.0},
            track_id=7,
        )

        event_service.record_event(event)

        # Receive WebSocket message
        msg = websocket.receive_json()
        assert msg["type"] == "event.created"
        data = msg["data"]
        assert data["event_id"] == event.event_id
        assert data["camera_id"] == "cam_ws_01"
        assert data["event_type"] == "restricted_zone_intrusion"
        assert data["track_id"] == "7"
        assert data["zone_id"] == "restricted_zone_A"
        assert data["confidence"] == 0.91
        assert data["bbox"]["x1"] == 120.0


def test_websocket_stream_disconnect_does_not_crash_publisher(app_and_client):
    app, client = app_and_client
    event_service = app.state.event_service
    publisher = app.state.event_publisher

    # 1. Connect and disconnect client 1
    with client.websocket_connect("/api/events/stream") as ws1:
        assert publisher.client_count == 1

    # Disconnected outside the with block
    assert publisher.client_count == 0

    # 2. Connect client 2
    with client.websocket_connect("/api/events/stream") as ws2:
        assert publisher.client_count == 1

        # Publish an event; should deliver without crash
        event = DomainEvent.create(
            camera_id="cam_01",
            event_type="restricted_zone_intrusion",
            object_class="person",
            zone_id="zone_test",
            confidence=0.88,
            bbox={"x1": 0, "y1": 0, "x2": 10, "y2": 10},
        )
        event_service.record_event(event)

        msg = ws2.receive_json()
        assert msg["type"] == "event.created"
        assert msg["data"]["event_id"] == event.event_id
