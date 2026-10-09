"""Unit tests for YOLODetector and inference normalization."""

import numpy as np
import pytest

from vision.detector import YOLODetector
from vision.exceptions import ModelLoadError
from vision.schemas import Detection


def test_detector_invalid_model():
    with pytest.raises(ModelLoadError) as exc_info:
        YOLODetector(model_name_or_path="non_existent_model_12345.pt")

    err_msg = str(exc_info.value)
    assert "Failed to load YOLO model" in err_msg
    assert "Actionable steps" in err_msg


def test_detector_valid_model_inference():
    # Load default model yolo11n.pt which is downloaded locally
    detector = YOLODetector(model_name_or_path="yolo11n.pt", confidence_threshold=0.25)
    assert len(detector.class_names) > 0
    assert 0 in detector.class_names  # 'person' in COCO

    # Run inference on synthetic blank frame
    blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detector.detect(blank_frame)

    assert isinstance(detections, list)
    for det in detections:
        assert isinstance(det, Detection)
        assert 0.0 <= det.confidence <= 1.0
        assert det.bbox.x1 <= det.bbox.x2
        assert det.bbox.y1 <= det.bbox.y2


def test_detector_empty_frame():
    detector = YOLODetector(model_name_or_path="yolo11n.pt")
    empty_frame = np.array([], dtype=np.uint8)
    detections = detector.detect(empty_frame)
    assert detections == []
