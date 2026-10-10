"""Unit tests for rules schemas and DomainEvent contract."""

import pytest

from rules.schemas import DomainEvent, ZoneState


def test_zone_state_values():
    assert ZoneState.OUTSIDE.value == "outside"
    assert ZoneState.INSIDE.value == "inside"
    assert ZoneState.UNKNOWN.value == "unknown"


def test_domain_event_creation_and_contract():
    event = DomainEvent.create(
        camera_id="cam_01",
        event_type="restricted_zone_intrusion",
        object_class="person",
        zone_id="restricted_zone_A",
        confidence=0.92346,
        bbox={"x1": 100.0, "y1": 50.0, "x2": 200.0, "y2": 300.0},
        track_id=12,
    )

    assert event.event_id.startswith("evt_")
    assert event.camera_id == "cam_01"
    assert event.event_type == "restricted_zone_intrusion"
    assert event.occurred_at.endswith("Z")
    assert event.object_class == "person"
    assert event.track_id == "12"
    assert event.confidence == 0.9235
    assert event.zone_id == "restricted_zone_A"
    assert event.snapshot_path is None

    # Serialization matches contract dictionary
    d = event.to_dict()
    assert d["event_id"] == event.event_id
    assert d["camera_id"] == "cam_01"
    assert d["event_type"] == "restricted_zone_intrusion"
    assert d["track_id"] == "12"
    assert d["zone_id"] == "restricted_zone_A"
    assert d["confidence"] == 0.9235


def test_domain_event_validation_errors():
    with pytest.raises(ValueError, match="confidence must be in range"):
        DomainEvent(
            event_id="evt_1",
            camera_id="cam_1",
            event_type="intrusion",
            occurred_at="2026-10-10T00:00:00Z",
            object_class="person",
            zone_id="zone_A",
            confidence=1.5,
            bbox={"x1": 0, "y1": 0, "x2": 10, "y2": 10},
        )

    with pytest.raises(ValueError, match="event_id must not be empty"):
        DomainEvent(
            event_id="",
            camera_id="cam_1",
            event_type="intrusion",
            occurred_at="2026-10-10T00:00:00Z",
            object_class="person",
            zone_id="zone_A",
            confidence=0.8,
            bbox={"x1": 0, "y1": 0, "x2": 10, "y2": 10},
        )
