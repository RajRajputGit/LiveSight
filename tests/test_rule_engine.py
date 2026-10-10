"""Unit tests for RuleEngine coordinator and configuration loading."""

import json
from pathlib import Path
import pytest

from rules.engine import RuleEngine
from rules.geometry import Polygon
from rules.restricted_zone import RestrictedZoneRule
from rules.schemas import DomainEvent
from vision.schemas import BoundingBox, Detection


def test_rule_engine_basic_evaluation():
    rule = RestrictedZoneRule(
        zone_id="zone_1",
        polygon=[(100, 100), (300, 100), (300, 300), (100, 300)],
    )
    engine = RuleEngine([rule])

    det_inside = Detection(
        class_id=0,
        class_name="person",
        confidence=0.89,
        bbox=BoundingBox(x1=150, y1=150, x2=250, y2=250),
        track_id=1,
    )

    events = engine.process([det_inside], frame_time=0.0, frame_idx=1, frame_dims=(640, 480))
    assert len(events) == 1
    assert engine.total_events_emitted == 1
    assert len(engine.history) == 1
    assert engine.history[0].zone_id == "zone_1"


def test_rule_engine_listener_dispatch():
    rule = RestrictedZoneRule(
        zone_id="zone_1",
        polygon=[(100, 100), (300, 100), (300, 300), (100, 300)],
    )
    engine = RuleEngine([rule])

    dispatched = []
    engine.add_listener(lambda ev: dispatched.append(ev))

    det = Detection(
        class_id=0,
        class_name="person",
        confidence=0.9,
        bbox=BoundingBox(x1=150, y1=150, x2=250, y2=250),
        track_id=2,
    )

    engine.process([det], frame_time=0.0, frame_idx=1, frame_dims=(640, 480))
    assert len(dispatched) == 1
    assert dispatched[0].track_id == "2"


def test_rule_engine_from_config_file(tmp_path: Path):
    cfg_data = {
        "zones": [
            {
                "zone_id": "zone_cfg_test",
                "name": "Test Zone",
                "polygon": [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]],
                "coordinate_type": "normalized",
                "target_classes": ["person"],
                "cooldown_seconds": 4.0,
            }
        ]
    }
    cfg_file = tmp_path / "test_rules.json"
    cfg_file.write_text(json.dumps(cfg_data))

    engine = RuleEngine.from_config_file(cfg_file)
    assert len(engine.rules) == 1
    rule = engine.rules[0]
    assert rule.zone_id == "zone_cfg_test"
    assert rule.name == "Test Zone"
    assert rule.cooldown_seconds == 4.0
    assert rule.polygon.is_normalized is True


def test_rule_engine_reset():
    rule = RestrictedZoneRule(
        zone_id="zone_1",
        polygon=[(100, 100), (300, 100), (300, 300), (100, 300)],
    )
    engine = RuleEngine([rule])
    det = Detection(
        class_id=0,
        class_name="person",
        confidence=0.9,
        bbox=BoundingBox(x1=150, y1=150, x2=250, y2=250),
        track_id=1,
    )
    engine.process([det], frame_time=0.0, frame_idx=1, frame_dims=(640, 480))
    assert engine.total_events_emitted == 1

    engine.reset()
    assert engine.total_events_emitted == 0
    assert len(engine.history) == 0
