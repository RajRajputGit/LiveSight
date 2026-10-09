"""LiveSight Vision Package - Phase 1: Real-Time Object Detection."""

from vision.schemas import BoundingBox, Detection
from vision.exceptions import VisionError, VideoSourceError, ModelLoadError, InferenceError
from vision.source import VideoSource
from vision.detector import YOLODetector
from vision.annotator import FrameAnnotator
from vision.pipeline import DetectionPipeline

__all__ = [
    "BoundingBox",
    "Detection",
    "VisionError",
    "VideoSourceError",
    "ModelLoadError",
    "InferenceError",
    "VideoSource",
    "YOLODetector",
    "FrameAnnotator",
    "DetectionPipeline",
]
