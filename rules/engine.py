"""Rule Engine coordinator for LiveSight (Phase 3).

Orchestrates rule evaluation, event dispatching, and in-memory history tracking.
Remains independent of database and web framework libraries as specified in ADR-003.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from rules.geometry import Polygon
from rules.restricted_zone import RestrictedZoneRule
from rules.schemas import DomainEvent
from vision.schemas import Detection


EventListener = Callable[[DomainEvent], None]


class RuleEngine:
    """Evaluates detections against configured domain rules and dispatches events."""

    def __init__(
        self,
        rules: Optional[Sequence[RestrictedZoneRule]] = None,
        max_history: int = 1000,
    ) -> None:
        """Initialize the rule engine.

        Args:
            rules: Initial list of rule instances.
            max_history: Maximum number of recent events to buffer in memory.
        """
        self._rules: List[RestrictedZoneRule] = list(rules) if rules else []
        self._listeners: List[EventListener] = []
        self._history: List[DomainEvent] = []
        self.max_history = max_history
        self._total_events: int = 0

    @property
    def rules(self) -> List[RestrictedZoneRule]:
        return list(self._rules)

    @property
    def total_events_emitted(self) -> int:
        return self._total_events

    @property
    def history(self) -> List[DomainEvent]:
        return list(self._history)

    def add_rule(self, rule: RestrictedZoneRule) -> None:
        """Register a new rule."""
        self._rules.append(rule)

    def add_listener(self, listener: EventListener) -> None:
        """Subscribe a callback to newly triggered domain events."""
        self._listeners.append(listener)

    def reset(self) -> None:
        """Reset state across all registered rules and clear history."""
        for rule in self._rules:
            rule.reset()
        self._history.clear()
        self._total_events = 0

    def process(
        self,
        detections: Sequence[Detection],
        frame_time: float,
        frame_idx: int,
        frame_dims: Tuple[int, int],
        camera_id: str = "local_camera_01",
    ) -> List[DomainEvent]:
        """Evaluate all registered rules on the current frame's detections.

        Args:
            detections: List of detections / tracks from vision pipeline.
            frame_time: Monotonic or video timestamp in seconds.
            frame_idx: Sequential frame index.
            frame_dims: (width, height) pixel dimensions of current frame.
            camera_id: Stable identifier for the video source.

        Returns:
            List of newly triggered DomainEvents.
        """
        new_events: List[DomainEvent] = []

        for rule in self._rules:
            rule_events = rule.evaluate(
                detections=detections,
                frame_time=frame_time,
                frame_idx=frame_idx,
                frame_dims=frame_dims,
                camera_id=camera_id,
            )
            new_events.extend(rule_events)

        # Record and dispatch new events
        for event in new_events:
            self._total_events += 1
            self._history.append(event)
            if len(self._history) > self.max_history:
                self._history.pop(0)

            for listener in self._listeners:
                try:
                    listener(event)
                except Exception:
                    # Listeners should not interrupt the processing pipeline
                    pass

        return new_events

    @classmethod
    def from_config_dict(cls, config: Dict[str, Any]) -> RuleEngine:
        """Factory creating a RuleEngine configured from a dictionary."""
        engine = cls()
        zones = config.get("zones", [])

        for z in zones:
            polygon_data = z.get("polygon")
            if not polygon_data:
                continue

            rule = RestrictedZoneRule(
                zone_id=z["zone_id"],
                polygon=polygon_data,
                name=z.get("name"),
                target_classes=z.get("target_classes", ["person"]),
                reference_point_type=z.get("reference_point", "bottom_center"),
                cooldown_seconds=float(z.get("cooldown_seconds", 5.0)),
                track_expiry_seconds=float(z.get("track_expiry_seconds", 2.0)),
                reacquire_generates_alert=bool(z.get("reacquire_generates_alert", False)),
                allow_untracked_events=bool(z.get("allow_untracked_events", True)),
                untracked_cooldown_seconds=float(z.get("untracked_cooldown_seconds", 5.0)),
                min_confidence=float(z.get("min_confidence", 0.3)),
            )
            engine.add_rule(rule)

        return engine

    @classmethod
    def from_config_file(cls, path: Union[str, Path]) -> RuleEngine:
        """Factory loading rules configuration from a JSON file."""
        file_path = Path(path).expanduser().resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"Rules configuration file not found at: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls.from_config_dict(data)
