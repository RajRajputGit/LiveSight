"""Integration tests for DetectionPipeline with RuleEngine."""

import numpy as np

from rules.engine import RuleEngine
from rules.restricted_zone import RestrictedZoneRule
from vision.annotator import FrameAnnotator
from vision.detector import YOLODetector
from vision.pipeline import DetectionPipeline
from vision.schemas import BoundingBox, Detection


def test_pipeline_with_rule_engine_integration():
    detector = YOLODetector("yolo11n.pt")
    annotator = FrameAnnotator()

    # Rule covering entire center: normalized coordinates [0.1, 0.1] to [0.9, 0.9]
    rule = RestrictedZoneRule(
        zone_id="center_zone",
        polygon=[[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]],
        target_classes=["person"],
    )
    engine = RuleEngine([rule])

    pipeline = DetectionPipeline(
        detector=detector,
        annotator=annotator,
        enable_tracking=True,
        rule_engine=engine,
    )

    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # 1. Backward-compatible call (return_events=False, default)
    res_3 = pipeline.process_frame(frame, return_events=False)
    assert len(res_3) == 3
    out_frame, dets, fps = res_3
    assert out_frame.shape == (480, 640, 3)

    # 2. Event-aware call (return_events=True)
    res_4 = pipeline.process_frame(frame, return_events=True)
    assert len(res_4) == 4
    out_frame, dets, fps, events = res_4
    assert isinstance(events, list)

    # 3. Reset pipeline clears engine state
    pipeline.reset_tracker()
    assert engine.total_events_emitted == 0
