"""Unit tests for DetectionPipeline and FrameAnnotator."""

import numpy as np

from vision.annotator import FrameAnnotator
from vision.detector import YOLODetector
from vision.pipeline import DetectionPipeline
from vision.schemas import BoundingBox, Detection


def test_annotator_draws_detections():
    annotator = FrameAnnotator()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    bbox = BoundingBox(x1=50.0, y1=50.0, x2=200.0, y2=250.0)
    det = Detection(class_id=0, class_name="person", confidence=0.88, bbox=bbox)

    annotated = annotator.annotate(
        frame=frame,
        detections=[det],
        fps=25.0,
        source_label="test_camera",
    )

    assert annotated.shape == frame.shape
    # Frame should have been modified with annotations (not all zero anymore)
    assert np.any(annotated > 0)


def test_pipeline_processing():
    detector = YOLODetector(model_name_or_path="yolo11n.pt", confidence_threshold=0.3)
    annotator = FrameAnnotator()
    pipeline = DetectionPipeline(detector=detector, annotator=annotator)

    frame = np.zeros((240, 320, 3), dtype=np.uint8)

    for _ in range(5):
        out_frame, detections, fps = pipeline.process_frame(
            frame=frame,
            source_label="unit_test",
            draw_annotations=True,
        )
        assert out_frame.shape == (240, 320, 3)
        assert isinstance(detections, list)

    assert pipeline.total_frames == 5
    assert pipeline.current_fps >= 0.0
    assert pipeline.overall_average_fps >= 0.0


def test_annotator_draws_track_id():
    annotator = FrameAnnotator()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    bbox = BoundingBox(x1=50.0, y1=50.0, x2=200.0, y2=250.0)
    det = Detection(class_id=0, class_name="person", confidence=0.88, bbox=bbox, track_id=42)

    annotated = annotator.annotate(
        frame=frame,
        detections=[det],
        fps=30.0,
        source_label="track_test",
    )

    assert annotated.shape == frame.shape
    assert np.any(annotated > 0)


def test_pipeline_tracking_toggle():
    detector = YOLODetector(model_name_or_path="yolo11n.pt")
    annotator = FrameAnnotator()
    frame = np.zeros((240, 320, 3), dtype=np.uint8)

    # 1. Tracking enabled
    pipeline_track = DetectionPipeline(
        detector=detector,
        annotator=annotator,
        enable_tracking=True,
        tracker_config="bytetrack.yaml",
    )
    assert pipeline_track.enable_tracking is True
    out_frame, dets, fps = pipeline_track.process_frame(frame)
    assert out_frame.shape == frame.shape
    pipeline_track.reset_tracker()

    # 2. Tracking disabled (detection only)
    pipeline_notrack = DetectionPipeline(
        detector=detector,
        annotator=annotator,
        enable_tracking=False,
    )
    assert pipeline_notrack.enable_tracking is False
    out_frame, dets, fps = pipeline_notrack.process_frame(frame)
    assert out_frame.shape == frame.shape

