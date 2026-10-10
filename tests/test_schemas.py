"""Unit tests for vision schemas and data contracts."""

import pytest
from vision.schemas import BoundingBox, Detection


def test_bounding_box_valid():
    bbox = BoundingBox(x1=10.0, y1=20.0, x2=110.0, y2=220.0)
    assert bbox.x1 == 10.0
    assert bbox.y1 == 20.0
    assert bbox.x2 == 110.0
    assert bbox.y2 == 220.0
    assert bbox.as_int_tuple() == (10, 20, 110, 220)
    assert bbox.to_dict() == {"x1": 10.0, "y1": 20.0, "x2": 110.0, "y2": 220.0}


def test_bounding_box_invalid_x():
    with pytest.raises(ValueError, match="x1 .* must be <= x2"):
        BoundingBox(x1=100.0, y1=20.0, x2=50.0, y2=220.0)


def test_bounding_box_invalid_y():
    with pytest.raises(ValueError, match="y1 .* must be <= y2"):
        BoundingBox(x1=10.0, y1=300.0, x2=110.0, y2=200.0)


def test_detection_valid():
    bbox = BoundingBox(x1=5.0, y1=10.0, x2=50.0, y2=100.0)
    det = Detection(class_id=0, class_name="person", confidence=0.8954, bbox=bbox)

    assert det.class_id == 0
    assert det.class_name == "person"
    assert det.confidence == 0.8954
    assert det.bbox == bbox

    data = det.to_dict()
    assert data["class_id"] == 0
    assert data["class_name"] == "person"
    assert data["confidence"] == 0.8954
    assert data["bbox"] == {"x1": 5.0, "y1": 10.0, "x2": 50.0, "y2": 100.0}


def test_detection_invalid_confidence():
    bbox = BoundingBox(x1=0, y1=0, x2=10, y2=10)
    with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
        Detection(class_id=0, class_name="person", confidence=1.5, bbox=bbox)

    with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
        Detection(class_id=0, class_name="person", confidence=-0.1, bbox=bbox)


def test_detection_with_track_id():
    bbox = BoundingBox(x1=5.0, y1=10.0, x2=50.0, y2=100.0)
    det = Detection(class_id=0, class_name="person", confidence=0.91, bbox=bbox, track_id=7)

    assert det.track_id == 7
    data = det.to_dict()
    assert data["track_id"] == 7


def test_detection_invalid_track_id_type():
    bbox = BoundingBox(x1=0, y1=0, x2=10, y2=10)
    with pytest.raises(TypeError, match="track_id must be an int or None"):
        Detection(class_id=0, class_name="person", confidence=0.5, bbox=bbox, track_id="invalid_id")

