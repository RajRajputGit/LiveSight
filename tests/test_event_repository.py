"""Unit and integration tests for SQLite EventRepository."""

from pathlib import Path
import pytest

from backend.app.repositories.event_repository import DatabaseError, EventRepository
from rules.schemas import DomainEvent


@pytest.fixture
def repo():
    """In-memory SQLite repository fixture."""
    return EventRepository(":memory:")


def test_repo_init_and_empty_list(repo):
    items, next_cursor = repo.list_events()
    assert items == []
    assert next_cursor is None
    assert repo.count() == 0


def test_repo_save_and_get_domain_event(repo):
    event = DomainEvent.create(
        camera_id="cam_01",
        event_type="restricted_zone_intrusion",
        object_class="person",
        zone_id="zone_A",
        confidence=0.88,
        bbox={"x1": 10.0, "y1": 20.0, "x2": 60.0, "y2": 120.0},
        track_id=5,
    )

    saved = repo.save(event)
    assert saved.event_id == event.event_id
    assert saved.camera_id == "cam_01"
    assert saved.track_id == "5"
    assert saved.bbox.x1 == 10.0

    retrieved = repo.get_by_id(event.event_id)
    assert retrieved is not None
    assert retrieved.event_id == event.event_id
    assert retrieved.confidence == 0.88
    assert retrieved.zone_id == "zone_A"
    assert retrieved.bbox.x2 == 60.0


def test_repo_save_from_dict(repo):
    event_dict = {
        "event_id": "evt_dict_1",
        "camera_id": "cam_02",
        "event_type": "restricted_zone_intrusion",
        "occurred_at": "2026-10-10T12:00:00.000Z",
        "object_class": "person",
        "confidence": 0.95,
        "zone_id": "zone_B",
        "track_id": None,
        "bbox": None,
        "snapshot_path": None,
    }
    saved = repo.save(event_dict)
    assert saved.event_id == "evt_dict_1"
    assert saved.bbox is None
    assert saved.track_id is None

    retrieved = repo.get_by_id("evt_dict_1")
    assert retrieved is not None
    assert retrieved.bbox is None


def test_repo_save_many_batch(repo):
    events = [
        DomainEvent.create(
            camera_id="cam_01",
            event_type="restricted_zone_intrusion",
            object_class="person",
            zone_id="zone_A",
            confidence=0.7 + i * 0.05,
            bbox={"x1": 10.0, "y1": 10.0, "x2": 50.0, "y2": 50.0},
            track_id=i,
            occurred_at=f"2026-10-10T12:00:0{i}.000Z",
        )
        for i in range(5)
    ]

    saved = repo.save_many(events)
    assert len(saved) == 5
    assert repo.count() == 5


def test_repo_duplicate_event_id_idempotent(repo):
    event = DomainEvent.create(
        camera_id="cam_01",
        event_type="restricted_zone_intrusion",
        object_class="person",
        zone_id="zone_A",
        confidence=0.9,
        bbox={"x1": 10, "y1": 20, "x2": 30, "y2": 40},
    )

    repo.save(event)
    # Second save with same event_id should succeed without error or duplicate row
    repo.save(event)
    assert repo.count() == 1


def test_repo_pagination_and_next_cursor(repo):
    # Seed 5 events with timestamps in ascending order
    for i in range(5):
        event = DomainEvent.create(
            camera_id="cam_01",
            event_type="restricted_zone_intrusion",
            object_class="person",
            zone_id="zone_A",
            confidence=0.8,
            bbox={"x1": 10, "y1": 20, "x2": 30, "y2": 40},
            track_id=i,
            occurred_at=f"2026-10-10T12:00:0{i}.000Z",
        )
        repo.save(event)

    # Page 1: limit=2 (should return newest events: index 4 and 3)
    page1, cursor1 = repo.list_events(limit=2)
    assert len(page1) == 2
    assert page1[0].track_id == "4"
    assert page1[1].track_id == "3"
    assert cursor1 == "2026-10-10T12:00:03.000Z"

    # Page 2: before=cursor1, limit=2 (should return index 2 and 1)
    page2, cursor2 = repo.list_events(limit=2, before=cursor1)
    assert len(page2) == 2
    assert page2[0].track_id == "2"
    assert page2[1].track_id == "1"
    assert cursor2 == "2026-10-10T12:00:01.000Z"

    # Page 3: before=cursor2, limit=2 (should return index 0, next_cursor None)
    page3, cursor3 = repo.list_events(limit=2, before=cursor2)
    assert len(page3) == 1
    assert page3[0].track_id == "0"
    assert cursor3 is None


def test_repo_filtering_by_type_and_camera(repo):
    repo.save(
        DomainEvent.create(
            camera_id="cam_A",
            event_type="restricted_zone_intrusion",
            object_class="person",
            zone_id="z1",
            confidence=0.9,
            bbox={"x1": 0, "y1": 0, "x2": 1, "y2": 1},
        )
    )
    repo.save(
        DomainEvent.create(
            camera_id="cam_B",
            event_type="restricted_zone_intrusion",
            object_class="person",
            zone_id="z2",
            confidence=0.9,
            bbox={"x1": 0, "y1": 0, "x2": 1, "y2": 1},
        )
    )

    items_cam_a, _ = repo.list_events(camera_id="cam_A")
    assert len(items_cam_a) == 1
    assert items_cam_a[0].camera_id == "cam_A"

    items_cam_b, _ = repo.list_events(camera_id="cam_B")
    assert len(items_cam_b) == 1
    assert items_cam_b[0].camera_id == "cam_B"

    items_nonexistent, _ = repo.list_events(camera_id="cam_NONEXISTENT")
    assert len(items_nonexistent) == 0


def test_repo_invalid_limit(repo):
    with pytest.raises(ValueError, match="limit must be between 1 and 100"):
        repo.list_events(limit=0)

    with pytest.raises(ValueError, match="limit must be between 1 and 100"):
        repo.list_events(limit=101)


def test_repo_events_survive_restart(tmp_path: Path):
    db_file = tmp_path / "test_persistence.db"

    # First repository instance
    repo1 = EventRepository(db_file)
    event = DomainEvent.create(
        camera_id="cam_persisted",
        event_type="restricted_zone_intrusion",
        object_class="person",
        zone_id="zone_safe",
        confidence=0.92,
        bbox={"x1": 10, "y1": 20, "x2": 30, "y2": 40},
        track_id=99,
    )
    repo1.save(event)
    assert repo1.count() == 1

    # Simulate backend restart with a new repository instance pointing to the same file
    repo2 = EventRepository(db_file)
    assert repo2.count() == 1
    loaded = repo2.get_by_id(event.event_id)
    assert loaded is not None
    assert loaded.track_id == "99"
    assert loaded.camera_id == "cam_persisted"
