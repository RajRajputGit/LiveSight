"""Custom exceptions for LiveSight vision module.

Designed to give clear, actionable diagnostic information to users and operators.
"""


class VisionError(Exception):
    """Base exception for all LiveSight vision errors."""


class VideoSourceError(VisionError):
    """Raised when opening, reading, or configuring a video source fails."""


class ModelLoadError(VisionError):
    """Raised when loading YOLO model weights or initializing inference fails."""


class InferenceError(VisionError):
    """Raised when running model inference fails."""
