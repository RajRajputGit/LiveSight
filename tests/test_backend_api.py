"""API integration tests for LiveSight FastAPI backend.

Tests endpoints:
- GET /api/health
- GET /api/status
- GET /api/events (filtering, pagination, validation, errors)
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app
from rules.schemas import DomainEvent


@pytest.fixture
def client(tmp_path: Path):
    """TestClient fixture with temporary SQLite database and pipeline worker disabled."""
    db_file = tmp_path / "api_test.db"

    test_settings = Settings()
    test_settings.database_path = str(db_file)
    test_settings.start_pipeline_on_startup = False

    app = create_app(custom_settings=test_settings)
    with TestClient(app) as test_client:
        yield test_client


def test_api_health_endpoint(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"status": "ok", "service": "ai-vision-backend"}


def test_api_status_endpoint_idle(client: TestClient):
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "pipeline_status" in data
    assert data["pipeline_status"] in ("idle", "stopped")
    assert data["model_loaded"] is False
    assert data["tracking_enabled"] is False
    assert data["last_frame_at"] is None
    assert data["last_error"] is None


def test_api_events_empty_history(client: TestClient):
    resp = client.get("/api/events")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"items": [], "next_cursor": None}


def test_api_events_seeded_history_and_filtering(client: TestClient):
    # Seed events through repository on app.state
    repo = client.app.state.repository
    e1 = DomainEvent.create(
        camera_id="cam_east",
        event_type="restricted_zone_intrusion",
        object_class="person",
        zone_id="zone_A",
        confidence=0.85,
        bbox={"x1": 10, "y1": 20, "x2": 50, "y2": 100},
        track_id=1,
        occurred_at="2026-10-10T10:00:00.000Z",
    )
    e2 = DomainEvent.create(
        camera_id="cam_west",
        event_type="restricted_zone_intrusion",
        object_class="person",
        zone_id="zone_B",
        confidence=0.92,
        bbox={"x1": 15, "y1": 25, "x2": 55, "y2": 105},
        track_id=2,
        occurred_at="2026-10-10T10:05:00.000Z",
    )
    repo.save(e1)
    repo.save(e2)

    # 1. Fetch all
    resp = client.get("/api/events")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    # Verify ordering: most recent first (e2 occurred at 10:05, e1 at 10:00)
    assert data["items"][0]["event_id"] == e2.event_id
    assert data["items"][1]["event_id"] == e1.event_id

    # 2. Filter by camera_id
    resp_cam = client.get("/api/events?camera_id=cam_east")
    assert resp_cam.status_code == 200
    cam_data = resp_cam.json()
    assert len(cam_data["items"]) == 1
    assert cam_data["items"][0]["camera_id"] == "cam_east"

    # 3. Filter by nonexistent camera
    resp_empty = client.get("/api/events?camera_id=cam_north")
    assert resp_empty.status_code == 200
    assert resp_empty.json()["items"] == []


def test_api_events_pagination(client: TestClient):
    repo = client.app.state.repository
    for i in range(5):
        repo.save(
            DomainEvent.create(
                camera_id="cam_01",
                event_type="restricted_zone_intrusion",
                object_class="person",
                zone_id="zone_A",
                confidence=0.8,
                bbox={"x1": 0, "y1": 0, "x2": 1, "y2": 1},
                track_id=i,
                occurred_at=f"2026-10-10T12:00:0{i}.000Z",
            )
        )

    # Page 1: limit 2
    r1 = client.get("/api/events?limit=2")
    assert r1.status_code == 200
    d1 = r1.json()
    assert len(d1["items"]) == 2
    assert d1["items"][0]["track_id"] == "4"
    assert d1["items"][1]["track_id"] == "3"
    cursor = d1["next_cursor"]
    assert cursor is not None

    # Page 2: with before cursor
    r2 = client.get(f"/api/events?limit=2&before={cursor}")
    assert r2.status_code == 200
    d2 = r2.json()
    assert len(d2["items"]) == 2
    assert d2["items"][0]["track_id"] == "2"
    assert d2["items"][1]["track_id"] == "1"


def test_api_events_invalid_limit_query_error_contract(client: TestClient):
    # Test limit=0 -> 400 Bad Request with standardized error envelope
    r0 = client.get("/api/events?limit=0")
    assert r0.status_code == 400
    assert r0.json() == {
        "error": {
            "code": "INVALID_QUERY",
            "message": "The limit parameter must be between 1 and 100.",
        }
    }

    # Test limit=150 -> 400 Bad Request
    r150 = client.get("/api/events?limit=150")
    assert r150.status_code == 400
    assert r150.json()["error"]["code"] == "INVALID_QUERY"


def test_api_http_error_response_contract(client: TestClient):
    # Non-existent endpoint -> 404 with standardized error envelope
    r = client.get("/api/nonexistent-endpoint")
    assert r.status_code == 404
    d = r.json()
    assert "error" in d
    assert d["error"]["code"] == "HTTP_ERROR"
