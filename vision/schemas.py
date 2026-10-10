"""Data contracts and schemas for LiveSight object detection.

Follows the detection contract defined in 03_WORKFLOW_AND_DATA_CONTRACTS.md:
- Pixel coordinates relative to original frame
- x1 <= x2 and y1 <= y2
- Confidence between 0.0 and 1.0
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class BoundingBox:
    """Bounding box in pixel coordinates (x1, y1, x2, y2)."""

    x1: float
    y1: float
    x2: float
    y2: float

    def __post_init__(self) -> None:
        """Validate box geometry."""
        if self.x1 > self.x2:
            raise ValueError(f"Invalid bounding box: x1 ({self.x1}) must be <= x2 ({self.x2})")
        if self.y1 > self.y2:
            raise ValueError(f"Invalid bounding box: y1 ({self.y1}) must be <= y2 ({self.y2})")

    def as_int_tuple(self) -> Tuple[int, int, int, int]:
        """Return integer coordinates (x1, y1, x2, y2) suitable for OpenCV rendering."""
        return (
            int(round(self.x1)),
            int(round(self.y1)),
            int(round(self.x2)),
            int(round(self.y2)),
        )

    def to_dict(self) -> Dict[str, float]:
        """Convert bounding box to serialized dictionary."""
        return {
            "x1": round(self.x1, 2),
            "y1": round(self.y1, 2),
            "x2": round(self.x2, 2),
            "y2": round(self.y2, 2),
        }


@dataclass(frozen=True)
class Detection:
    """Normalized object detection representation with optional tracking ID."""

    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox
    track_id: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate detection fields."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )
        if self.track_id is not None and not isinstance(self.track_id, int):
            raise TypeError(
                f"track_id must be an int or None, got {type(self.track_id).__name__}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert detection to normalized contract dictionary."""
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": round(self.confidence, 4),
            "bbox": self.bbox.to_dict(),
            "track_id": self.track_id,
        }


# Track contract alias conforming to 03_WORKFLOW_AND_DATA_CONTRACTS.md
Track = Detection

