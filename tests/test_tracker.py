"""Unit tests for ByteTrackerAdapter and tracker lifecycle management."""

from pathlib import Path
import numpy as np
import pytest

from vision.detector import YOLODetector
from vision.schemas import BoundingBox, Detection
from vision.tracker import ByteTrackerAdapter, TrackerError


def test_tracker_adapter_valid_config():
    adapter = ByteTrackerAdapter("bytetrack.yaml")
    assert adapter.tracker_config == "bytetrack.yaml"
    assert adapter.persist is True


def test_tracker_adapter_empty_config():
    with pytest.raises(TrackerError, match="cannot be empty"):
        ByteTrackerAdapter("")


def test_tracker_adapter_missing_file_config():
    with pytest.raises(TrackerError, match="Tracker configuration file not found"):
        ByteTrackerAdapter("configs/non_existent_tracker.yaml")


def test_tracker_adapter_reset():
    adapter = ByteTrackerAdapter()
    # Resetting without model should complete without error
    adapter.reset(model=None)


def test_detector_track_on_blank_frame():
    detector = YOLODetector(model_name_or_path="yolo11n.pt", confidence_threshold=0.25)
    blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Calling track with ByteTrack on blank frame
    detections = detector.track(blank_frame, tracker="bytetrack.yaml", persist=True)
    assert isinstance(detections, list)
    for det in detections:
        assert isinstance(det, Detection)
        # track_id may be None or int
        assert det.track_id is None or isinstance(det.track_id, int)


def test_detector_reset_tracker():
    detector = YOLODetector(model_name_or_path="yolo11n.pt")
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Run track once to initialize predictor and tracker
    detector.track(frame, tracker="bytetrack.yaml", persist=True)

    # Calling reset_tracker should reset state cleanly
    detector.reset_tracker()


def test_detector_missing_id_handling():
    detector = YOLODetector(model_name_or_path="yolo11n.pt")

    # Mock boxes object where id is None
    class MockBoxes:
        def __init__(self):
            self.id = None
            self.xyxy = [[10.0, 20.0, 50.0, 60.0]]
            self.conf = [0.85]
            self.cls = [0]

        def __len__(self):
            return 1

        def __iter__(self):
            class MockBox:
                xyxy = [[10.0, 20.0, 50.0, 60.0]]
                conf = [0.85]
                cls = [0]
            yield MockBox()

    parsed = detector._parse_boxes(MockBoxes(), has_tracking=True)
    assert len(parsed) == 1
    assert parsed[0].track_id is None
    assert parsed[0].confidence == 0.85
    assert parsed[0].class_id == 0
