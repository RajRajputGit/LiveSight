"""Event and state schemas for LiveSight rules engine.

Follows the Event Contract defined in 03_WORKFLOW_AND_DATA_CONTRACTS.md:
- event_id: unique event identifier
- camera_id: stable source identifier
- event_type: machine-readable event name (e.g. 'restricted_zone_intrusion')
- occurred_at: UTC timestamp with timezone
- object_class: object class name
- track_id: optional track identifier
- confidence: float score
- zone_id: rule zone identifier
- bbox: bounding box dictionary {x1, y1, x2, y2}
- snapshot_path: optional asset path or None
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Union
import uuid


class ZoneState(str, Enum):
    """Tracking state relative to a restricted zone."""

    OUTSIDE = "outside"
    INSIDE = "inside"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DomainEvent:
    """Structured domain event produced by the rule engine."""

    event_id: str
    camera_id: str
    event_type: str
    occurred_at: str
    object_class: str
    zone_id: str
    confidence: float
    bbox: Dict[str, float]
    track_id: Optional[Union[int, str]] = None
    snapshot_path: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate required fields according to event contract."""
        if not self.event_id:
            raise ValueError("event_id must not be empty.")
        if not self.camera_id:
            raise ValueError("camera_id must not be empty.")
        if not self.event_type:
            raise ValueError("event_type must not be empty.")
        if not self.zone_id:
            raise ValueError("zone_id must not be empty.")
        if not self.object_class:
            raise ValueError("object_class must not be empty.")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be in range [0.0, 1.0], got {self.confidence}")

    @classmethod
    def create(
        cls,
        camera_id: str,
        event_type: str,
        object_class: str,
        zone_id: str,
        confidence: float,
        bbox: Dict[str, float],
        track_id: Optional[Union[int, str]] = None,
        snapshot_path: Optional[str] = None,
        occurred_at: Optional[str] = None,
        event_id: Optional[str] = None,
    ) -> DomainEvent:
        """Factory method generating standard UTC ISO-8601 timestamps and unique IDs."""
        if event_id is None:
            event_id = f"evt_{uuid.uuid4().hex[:12]}"

        if occurred_at is None:
            # Format: 2026-10-10T12:00:00.000Z
            now_utc = datetime.now(timezone.utc)
            occurred_at = now_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        # Format track_id consistently as string if integer provided
        formatted_track_id = str(track_id) if track_id is not None else None

        return cls(
            event_id=event_id,
            camera_id=camera_id,
            event_type=event_type,
            occurred_at=occurred_at,
            object_class=object_class,
            zone_id=zone_id,
            confidence=round(float(confidence), 4),
            bbox=bbox,
            track_id=formatted_track_id,
            snapshot_path=snapshot_path,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to serialized contract dictionary."""
        return {
            "event_id": self.event_id,
            "camera_id": self.camera_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "object_class": self.object_class,
            "track_id": self.track_id,
            "confidence": self.confidence,
            "zone_id": self.zone_id,
            "bbox": self.bbox,
            "snapshot_path": self.snapshot_path,
        }
