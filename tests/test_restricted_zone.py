"""Unit tests for RestrictedZoneRule state machine and duplicate prevention."""

import pytest

from rules.geometry import Polygon
from rules.restricted_zone import RestrictedZoneRule
from rules.schemas import ZoneState
from vision.schemas import BoundingBox, Detection


@pytest.fixture
def zone_rule():
    # Square zone in frame coordinates: (100, 100) to (300, 300)
    polygon = Polygon([(100, 100), (300, 100), (300, 300), (100, 300)])
    return RestrictedZoneRule(
        zone_id="test_zone",
        polygon=polygon,
        target_classes=["person"],
        cooldown_seconds=3.0,
        track_expiry_seconds=1.0,
        reacquire_generates_alert=False,
    )


def test_outside_to_inside_triggers_event(zone_rule):
    # Frame 1: Person track 1 outside zone (bottom-center at (50, 50))
    det_outside = Detection(
        class_id=0,
        class_name="person",
        confidence=0.85,
        bbox=BoundingBox(x1=30, y1=10, x2=70, y2=50),
        track_id=1,
    )
    events_1 = zone_rule.evaluate([det_outside], frame_time=0.0, frame_idx=1, frame_dims=(640, 480))
    assert len(events_1) == 0
    assert zone_rule._tracks["1"].state == ZoneState.OUTSIDE

    # Frame 2: Person track 1 enters zone (bottom-center at (200, 200))
    det_inside = Detection(
        class_id=0,
        class_name="person",
        confidence=0.90,
        bbox=BoundingBox(x1=180, y1=150, x2=220, y2=200),
        track_id=1,
    )
    events_2 = zone_rule.evaluate([det_inside], frame_time=0.1, frame_idx=2, frame_dims=(640, 480))
    assert len(events_2) == 1
    ev = events_2[0]
    assert ev.event_type == "restricted_zone_intrusion"
    assert ev.track_id == "1"
    assert ev.zone_id == "test_zone"
    assert zone_rule._tracks["1"].state == ZoneState.INSIDE


def test_inside_to_inside_suppresses_duplicates(zone_rule):
    # Person enters zone at frame 1
    det_inside = Detection(
        class_id=0,
        class_name="person",
        confidence=0.90,
        bbox=BoundingBox(x1=180, y1=150, x2=220, y2=200),
        track_id=1,
    )
    events_1 = zone_rule.evaluate([det_inside], frame_time=0.0, frame_idx=1, frame_dims=(640, 480))
    assert len(events_1) == 1

    # Person remains inside for subsequent 30 frames
    for i in range(2, 32):
        t = i * 0.033
        events = zone_rule.evaluate([det_inside], frame_time=t, frame_idx=i, frame_dims=(640, 480))
        assert len(events) == 0, f"Duplicate event generated at frame {i}"


def test_exit_and_reentry_cooldown(zone_rule):
    # 1. Enters zone at t=0.0 -> Alert 1
    det_inside = Detection(
        class_id=0,
        class_name="person",
        confidence=0.90,
        bbox=BoundingBox(x1=180, y1=150, x2=220, y2=200),
        track_id=1,
    )
    events_1 = zone_rule.evaluate([det_inside], frame_time=0.0, frame_idx=1, frame_dims=(640, 480))
    assert len(events_1) == 1

    # 2. Exits zone at t=0.5
    det_outside = Detection(
        class_id=0,
        class_name="person",
        confidence=0.85,
        bbox=BoundingBox(x1=30, y1=10, x2=70, y2=50),
        track_id=1,
    )
    events_2 = zone_rule.evaluate([det_outside], frame_time=0.5, frame_idx=2, frame_dims=(640, 480))
    assert len(events_2) == 0
    assert zone_rule._tracks["1"].state == ZoneState.OUTSIDE

    # 3. Re-enters at t=1.0 (before cooldown_seconds=3.0 expires) -> Alert suppressed
    events_3 = zone_rule.evaluate([det_inside], frame_time=1.0, frame_idx=3, frame_dims=(640, 480))
    assert len(events_3) == 0

    # 4. Exits again at t=2.0
    zone_rule.evaluate([det_outside], frame_time=2.0, frame_idx=4, frame_dims=(640, 480))

    # 5. Re-enters at t=4.0 (after cooldown 3.0s has passed since t=0.0) -> Alert 2 triggered!
    events_5 = zone_rule.evaluate([det_inside], frame_time=4.0, frame_idx=5, frame_dims=(640, 480))
    assert len(events_5) == 1


def test_track_expiry_and_reacquisition(zone_rule):
    # Track enters zone at t=0.0
    det_inside = Detection(
        class_id=0,
        class_name="person",
        confidence=0.90,
        bbox=BoundingBox(x1=180, y1=150, x2=220, y2=200),
        track_id=5,
    )
    zone_rule.evaluate([det_inside], frame_time=0.0, frame_idx=1, frame_dims=(640, 480))
    assert zone_rule._tracks["5"].state == ZoneState.INSIDE

    # Track disappears for 1.5 seconds (track_expiry_seconds=1.0)
    # Empty detections evaluate at t=1.5
    zone_rule.evaluate([], frame_time=1.5, frame_idx=2, frame_dims=(640, 480))
    assert zone_rule._tracks["5"].state == ZoneState.UNKNOWN

    # Track re-appears directly inside at t=2.0
    # With reacquire_generates_alert=False (default conservative policy), no duplicate alert
    events = zone_rule.evaluate([det_inside], frame_time=2.0, frame_idx=3, frame_dims=(640, 480))
    assert len(events) == 0
    assert zone_rule._tracks["5"].state == ZoneState.INSIDE


def test_untracked_detection_fallback(zone_rule):
    # Detection with track_id=None inside zone
    det_untracked = Detection(
        class_id=0,
        class_name="person",
        confidence=0.88,
        bbox=BoundingBox(x1=180, y1=150, x2=220, y2=200),
        track_id=None,
    )

    # First intrusion -> Alert
    events_1 = zone_rule.evaluate([det_untracked], frame_time=0.0, frame_idx=1, frame_dims=(640, 480))
    assert len(events_1) == 1
    assert events_1[0].track_id is None

    # Immediate next frame at t=0.033 -> Debounced / suppressed
    events_2 = zone_rule.evaluate([det_untracked], frame_time=0.033, frame_idx=2, frame_dims=(640, 480))
    assert len(events_2) == 0


def test_target_class_filtering(zone_rule):
    # Non-target class (e.g. dog or car) inside zone should not trigger event
    det_car = Detection(
        class_id=2,
        class_name="car",
        confidence=0.90,
        bbox=BoundingBox(x1=180, y1=150, x2=220, y2=200),
        track_id=10,
    )
    events = zone_rule.evaluate([det_car], frame_time=0.0, frame_idx=1, frame_dims=(640, 480))
    assert len(events) == 0


def test_rule_reset(zone_rule):
    det_inside = Detection(
        class_id=0,
        class_name="person",
        confidence=0.90,
        bbox=BoundingBox(x1=180, y1=150, x2=220, y2=200),
        track_id=1,
    )
    zone_rule.evaluate([det_inside], frame_time=0.0, frame_idx=1, frame_dims=(640, 480))
    assert len(zone_rule._tracks) == 1

    zone_rule.reset()
    assert len(zone_rule._tracks) == 0
    assert zone_rule.get_active_inside_tracks() == []
