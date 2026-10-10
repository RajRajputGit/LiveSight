"""Deterministic Restricted-Zone intrusion rule evaluation and state machine.

Follows the Restricted-Zone rule contract from:
- 01_PRODUCT_REQUIREMENTS.md (FR-04, FR-05)
- 03_WORKFLOW_AND_DATA_CONTRACTS.md (Section 5 & 6)
- 04_IMPLEMENTATION_PLAN.md (Phase 3)

Key behaviors:
1. Reference point calculation (default: bottom-center).
2. Outside -> Inside transition generates a domain event.
3. Inside -> Inside maintains inside state without generating per-frame duplicate events.
4. Inside -> Outside marks track as outside; subsequent re-entry can generate an alert.
5. Inside -> Unknown expires track state when lost beyond timeout.
6. Safe fallback for untracked detections with cooldown to prevent alert storms.
7. Tracker reset safely clears all active state records.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple, Union

from rules.geometry import Point, Polygon, get_reference_point
from rules.schemas import DomainEvent, ZoneState
from vision.schemas import BoundingBox, Detection


@dataclass
class TrackStateRecord:
    """Maintains continuous tracking state for a specific track ID."""

    track_id: str
    state: ZoneState = ZoneState.OUTSIDE
    last_seen_time: float = 0.0
    last_seen_frame: int = 0
    last_alert_time: Optional[float] = None
    last_position: Optional[Point] = None


class RestrictedZoneRule:
    """Configurable restricted polygon zone evaluating object intrusions."""

    def __init__(
        self,
        zone_id: str,
        polygon: Union[Polygon, Sequence[Sequence[float]]],
        name: Optional[str] = None,
        target_classes: Optional[Sequence[str]] = None,
        reference_point_type: str = "bottom_center",
        cooldown_seconds: float = 5.0,
        track_expiry_seconds: float = 2.0,
        reacquire_generates_alert: bool = False,
        allow_untracked_events: bool = True,
        untracked_cooldown_seconds: float = 5.0,
        min_confidence: float = 0.3,
    ) -> None:
        """Initialize the restricted zone rule.

        Args:
            zone_id: Unique identifier for the zone (e.g. 'restricted_zone_A').
            polygon: Polygon instance or sequence of [x, y] coordinates.
            name: Human-friendly name for reporting.
            target_classes: Set of object classes that trigger the rule (default: {'person'}).
            reference_point_type: Reference point convention ('bottom_center', 'center').
            cooldown_seconds: Cooldown period before the same track can re-trigger on re-entry.
            track_expiry_seconds: Timeout after which an unseen inside track transitions to UNKNOWN.
            reacquire_generates_alert: Whether reacquiring a lost track directly inside generates an alert.
            allow_untracked_events: Whether to emit an alert for detections lacking a track ID.
            untracked_cooldown_seconds: Minimum interval between untracked intrusion alerts.
            min_confidence: Minimum detection confidence to consider.
        """
        self.zone_id = str(zone_id).strip()
        if not self.zone_id:
            raise ValueError("zone_id must not be empty.")

        self.name = name or self.zone_id

        if isinstance(polygon, Polygon):
            self.polygon = polygon
        else:
            # Check if all coordinates in sequence are within [0, 1] to auto-detect normalization
            is_norm = all(
                0.0 <= float(p[0]) <= 1.0 and 0.0 <= float(p[1]) <= 1.0
                for p in polygon
            )
            self.polygon = Polygon(polygon, is_normalized=is_norm)

        self.target_classes: Set[str] = (
            set(c.strip().lower() for c in target_classes)
            if target_classes
            else {"person"}
        )
        self.reference_point_type = reference_point_type
        self.cooldown_seconds = float(cooldown_seconds)
        self.track_expiry_seconds = float(track_expiry_seconds)
        self.reacquire_generates_alert = bool(reacquire_generates_alert)
        self.allow_untracked_events = bool(allow_untracked_events)
        self.untracked_cooldown_seconds = float(untracked_cooldown_seconds)
        self.min_confidence = float(min_confidence)

        # Per-track state registry: track_id -> TrackStateRecord
        self._tracks: Dict[str, TrackStateRecord] = {}
        self._last_untracked_alert_time: float = -9999.0

    def reset(self) -> None:
        """Reset all active track states and alert cooldowns (e.g. on stream restart)."""
        self._tracks.clear()
        self._last_untracked_alert_time = -9999.0

    def get_pixel_polygon(self, width: int, height: int) -> Polygon:
        """Get the polygon scaled to concrete pixel dimensions."""
        return self.polygon.to_pixel_coordinates(width, height)

    def get_active_inside_tracks(self) -> List[str]:
        """Return list of track IDs currently recorded inside the zone."""
        return [
            tid
            for tid, rec in self._tracks.items()
            if rec.state == ZoneState.INSIDE
        ]

    def evaluate(
        self,
        detections: Sequence[Detection],
        frame_time: float,
        frame_idx: int,
        frame_dims: Tuple[int, int],
        camera_id: str = "local_camera_01",
    ) -> List[DomainEvent]:
        """Evaluate detections against the zone rule and emit state-transition events.

        Args:
            detections: Sequence of Detection instances in the current frame.
            frame_time: Current timestamp (seconds, e.g. monotonic or video time).
            frame_idx: Sequential frame index.
            frame_dims: (width, height) in pixels.
            camera_id: Stable identifier of the active video source.

        Returns:
            List of generated DomainEvent instances (empty if no new trigger).
        """
        width, height = frame_dims
        pixel_poly = self.get_pixel_polygon(width, height)
        events: List[DomainEvent] = []
        observed_track_ids: Set[str] = set()

        # 1. Process each detection
        for det in detections:
            # Filter class and confidence
            if det.class_name.lower() not in self.target_classes:
                continue
            if det.confidence < self.min_confidence:
                continue

            ref_point = get_reference_point(
                det.bbox, reference_type=self.reference_point_type
            )
            is_inside = pixel_poly.contains_point(ref_point, on_boundary_inside=True)

            if det.track_id is not None:
                # --- Tracked Object Processing ---
                tid = str(det.track_id)
                observed_track_ids.add(tid)
                event = self._process_tracked_object(
                    track_id=tid,
                    detection=det,
                    ref_point=ref_point,
                    is_inside=is_inside,
                    frame_time=frame_time,
                    frame_idx=frame_idx,
                    camera_id=camera_id,
                )
                if event:
                    events.append(event)
            else:
                # --- Untracked Object Fallback ---
                if is_inside and self.allow_untracked_events:
                    event = self._process_untracked_object(
                        detection=det,
                        frame_time=frame_time,
                        camera_id=camera_id,
                    )
                    if event:
                        events.append(event)

        # 2. Expire tracks that were not observed in this frame
        self._expire_stale_tracks(
            observed_track_ids=observed_track_ids,
            current_time=frame_time,
        )

        return events

    def _process_tracked_object(
        self,
        track_id: str,
        detection: Detection,
        ref_point: Point,
        is_inside: bool,
        frame_time: float,
        frame_idx: int,
        camera_id: str,
    ) -> Optional[DomainEvent]:
        """Update state machine for a tracked object and trigger event on outside->inside."""
        rec = self._tracks.get(track_id)
        if rec is None:
            # First time seeing this track ID
            rec = TrackStateRecord(
                track_id=track_id,
                state=ZoneState.OUTSIDE,
                last_seen_time=frame_time,
                last_seen_frame=frame_idx,
                last_position=ref_point,
            )
            self._tracks[track_id] = rec

        prev_state = rec.state
        event: Optional[DomainEvent] = None

        if is_inside:
            should_alert = False

            if prev_state == ZoneState.OUTSIDE:
                # Clean Outside -> Inside transition!
                should_alert = True
            elif prev_state == ZoneState.UNKNOWN:
                # Track lost beyond timeout and reacquired directly inside
                if self.reacquire_generates_alert:
                    should_alert = True
            elif prev_state == ZoneState.INSIDE:
                # Inside -> Inside: remains inside, suppress duplicate
                should_alert = False

            # Check cooldown against previous alert for this track
            if should_alert and rec.last_alert_time is not None:
                if (frame_time - rec.last_alert_time) < self.cooldown_seconds:
                    should_alert = False

            if should_alert:
                event = DomainEvent.create(
                    camera_id=camera_id,
                    event_type="restricted_zone_intrusion",
                    object_class=detection.class_name,
                    zone_id=self.zone_id,
                    confidence=detection.confidence,
                    bbox=detection.bbox.to_dict(),
                    track_id=track_id,
                )
                rec.last_alert_time = frame_time

            rec.state = ZoneState.INSIDE

        else:
            # Outside the zone
            rec.state = ZoneState.OUTSIDE

        rec.last_seen_time = frame_time
        rec.last_seen_frame = frame_idx
        rec.last_position = ref_point
        return event

    def _process_untracked_object(
        self,
        detection: Detection,
        frame_time: float,
        camera_id: str,
    ) -> Optional[DomainEvent]:
        """Emit alert for an untracked detection inside zone, subject to cooldown."""
        if (frame_time - self._last_untracked_alert_time) >= self.untracked_cooldown_seconds:
            self._last_untracked_alert_time = frame_time
            return DomainEvent.create(
                camera_id=camera_id,
                event_type="restricted_zone_intrusion",
                object_class=detection.class_name,
                zone_id=self.zone_id,
                confidence=detection.confidence,
                bbox=detection.bbox.to_dict(),
                track_id=None,
            )
        return None

    def _expire_stale_tracks(
        self,
        observed_track_ids: Set[str],
        current_time: float,
    ) -> None:
        """Expire tracks that have disappeared beyond track_expiry_seconds."""
        for tid, rec in list(self._tracks.items()):
            if tid not in observed_track_ids:
                elapsed = current_time - rec.last_seen_time
                if elapsed > self.track_expiry_seconds:
                    if rec.state == ZoneState.INSIDE:
                        # Inside -> Unknown transition
                        rec.state = ZoneState.UNKNOWN

                # Clean up tracks unseen for more than 120 seconds to prevent unbounded memory
                if elapsed > 120.0:
                    del self._tracks[tid]
