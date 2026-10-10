"""LiveSight Vision Package - Phase 1 & 2: Object Detection and Multi-Object Tracking."""

from vision.schemas import BoundingBox, Detection, Track
from vision.exceptions import VisionError, VideoSourceError, ModelLoadError, InferenceError
from vision.source import VideoSource
from vision.detector import YOLODetector
from vision.annotator import FrameAnnotator
from vision.pipeline import DetectionPipeline
from vision.tracker import ByteTrackerAdapter, TrackerError

__all__ = [
    "BoundingBox",
    "Detection",
    "Track",
    "VisionError",
    "VideoSourceError",
    "ModelLoadError",
    "InferenceError",
    "TrackerError",
    "VideoSource",
    "YOLODetector",
    "ByteTrackerAdapter",
    "FrameAnnotator",
    "DetectionPipeline",
]

