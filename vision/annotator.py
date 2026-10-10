"""Visual annotation utilities for rendering detections and diagnostic overlays."""

from __future__ import annotations
from typing import List, Optional, Tuple

import cv2
import numpy as np

from vision.schemas import Detection


# Distinct color palette (BGR) for consistent, aesthetic class rendering
DEFAULT_COLORS: List[Tuple[int, int, int]] = [
    (0, 204, 255),   # Bright yellow/gold
    (0, 165, 255),   # Orange
    (75, 180, 60),   # Green
    (238, 130, 238), # Violet
    (255, 191, 0),   # Cyan/Deep Sky Blue
    (0, 215, 255),   # Amber
    (147, 20, 255),  # Pink/Magenta
    (205, 90, 106),  # Slate Blue
    (50, 205, 50),   # Lime green
    (230, 216, 173), # Light blue
]


def get_class_color(class_id: int) -> Tuple[int, int, int]:
    """Return a deterministic BGR color for a given class ID."""
    return DEFAULT_COLORS[class_id % len(DEFAULT_COLORS)]


def get_detection_color(class_id: int, track_id: Optional[int] = None) -> Tuple[int, int, int]:
    """Return a deterministic BGR color based on track ID (preferred) or class ID."""
    key = track_id if track_id is not None else class_id
    return DEFAULT_COLORS[key % len(DEFAULT_COLORS)]


class FrameAnnotator:
    """Renders bounding boxes, class labels, track IDs, confidence scores, and diagnostic HUD on frames."""

    def __init__(
        self,
        box_thickness: int = 2,
        font_scale: float = 0.55,
        font_thickness: int = 1,
    ) -> None:
        self.box_thickness = box_thickness
        self.font_scale = font_scale
        self.font_thickness = font_thickness
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def annotate(
        self,
        frame: np.ndarray,
        detections: List[Detection],
        fps: Optional[float] = None,
        source_label: Optional[str] = None,
        rules: Optional[Sequence[Any]] = None,
        events: Optional[Sequence[Any]] = None,
    ) -> np.ndarray:
        """Annotate frame with bounding boxes, track IDs, labels, zones, and HUD.

        Args:
            frame: Input BGR image array.
            detections: List of Detection instances (with optional track_id).
            fps: Optional current/smoothed FPS value to display.
            source_label: Optional source descriptor (e.g. 'Webcam [0]' or 'sample.mp4').
            rules: Optional list of RestrictedZoneRule instances to draw.
            events: Optional newly triggered DomainEvent instances to highlight.

        Returns:
            Annotated frame.
        """
        output = frame.copy()
        height, width = output.shape[:2]

        # 0. Draw configured restricted zones first (underneath bounding boxes)
        if rules:
            self._draw_zones(output, rules, events or [])

        # 1. Draw each detection / track
        for det in detections:
            x1, y1, x2, y2 = det.bbox.as_int_tuple()
            color = get_detection_color(det.class_id, det.track_id)

            # Draw bounding box
            cv2.rectangle(output, (x1, y1), (x2, y2), color, self.box_thickness)

            # Format label: with track ID if available ("#3 person 0.85"), otherwise ("person 0.85")
            if det.track_id is not None:
                label = f"#{det.track_id} {det.class_name} {det.confidence:.2f}"
            else:
                label = f"{det.class_name} {det.confidence:.2f}"

            (text_w, text_h), baseline = cv2.getTextSize(
                label, self.font, self.font_scale, self.font_thickness
            )

            # Calculate label background position (above box if space allows, otherwise inside)
            label_y1 = max(0, y1 - text_h - baseline - 6)
            label_y2 = label_y1 + text_h + baseline + 6
            label_x2 = min(output.shape[1], x1 + text_w + 8)

            # Draw filled rectangle for label background
            cv2.rectangle(output, (x1, label_y1), (label_x2, label_y2), color, -1)

            # Draw text inside background (use dark text for bright backgrounds)
            text_color = (20, 20, 20)
            text_pos = (x1 + 4, label_y2 - baseline - 3)
            cv2.putText(
                output,
                label,
                text_pos,
                self.font,
                self.font_scale,
                text_color,
                self.font_thickness,
                lineType=cv2.LINE_AA,
            )

        # 2. Draw diagnostic HUD badge in top-left corner
        tracked_count = sum(1 for d in detections if d.track_id is not None)
        alert_count = len(events) if events else 0
        self._draw_hud(output, fps, len(detections), tracked_count, alert_count, source_label)

        return output

    def _draw_zones(
        self,
        frame: np.ndarray,
        rules: Sequence[Any],
        events: Sequence[Any],
    ) -> None:
        """Render polygon zones and zone status on the frame."""
        h, w = frame.shape[:2]
        event_zone_ids = {getattr(e, "zone_id", None) for e in events}

        overlay = frame.copy()

        for rule in rules:
            if not hasattr(rule, "get_pixel_polygon"):
                continue

            pixel_poly = rule.get_pixel_polygon(w, h)
            pts = np.array(pixel_poly.as_numpy_points(), np.int32).reshape((-1, 1, 2))

            # Has intrusion alert in this frame or active inside tracks?
            has_inside_tracks = bool(getattr(rule, "get_active_inside_tracks", lambda: [])())
            has_alert = getattr(rule, "zone_id", None) in event_zone_ids or has_inside_tracks

            if has_alert:
                border_color = (0, 0, 255)       # Red for active intrusion
                fill_color = (0, 0, 200)
                status_text = f"ZONE: {rule.name} [ALERT]"
            else:
                border_color = (255, 180, 0)     # Cyan/Amber for safe monitoring
                fill_color = (200, 120, 0)
                status_text = f"ZONE: {rule.name}"

            # Semi-transparent polygon fill
            cv2.fillPoly(overlay, [pts], fill_color)

            # Polygon outline
            cv2.polylines(frame, [pts], isClosed=True, color=border_color, thickness=2)

            # Draw zone label
            if len(pixel_poly.vertices) > 0:
                first_pt = pixel_poly.vertices[0]
                label_pos = (max(10, int(first_pt.x)), max(25, int(first_pt.y) - 8))
                cv2.putText(
                    frame,
                    status_text,
                    label_pos,
                    self.font,
                    0.45,
                    border_color,
                    1,
                    lineType=cv2.LINE_AA,
                )

        # Blend overlay (alpha = 0.25)
        cv2.addWeighted(overlay, 0.22, frame, 0.78, 0, frame)

    def _draw_hud(
        self,
        frame: np.ndarray,
        fps: Optional[float],
        detection_count: int,
        tracked_count: int,
        alert_count: int,
        source_label: Optional[str],
    ) -> None:
        """Draw diagnostic telemetry banner on top-left of the frame."""
        hud_lines: List[str] = []

        if fps is not None:
            hud_lines.append(f"FPS: {fps:5.1f}")
        else:
            hud_lines.append("FPS: --.-")

        hud_lines.append(f"Objects: {detection_count}")
        if tracked_count > 0:
            hud_lines.append(f"Tracks: {tracked_count}")

        if alert_count > 0:
            hud_lines.append(f"Alerts: {alert_count}")

        if source_label:
            hud_lines.append(f"Source: {source_label}")



        hud_text = "  |  ".join(hud_lines)
        hint_text = "Press 'q' to quit"

        # Background dimensions
        padding_x = 10
        padding_y = 6
        (w1, h1), _ = cv2.getTextSize(hud_text, self.font, 0.55, 1)
        (w2, h2), _ = cv2.getTextSize(hint_text, self.font, 0.45, 1)

        box_w = max(w1, w2) + (padding_x * 2)
        box_h = h1 + h2 + (padding_y * 3) + 4

        # Draw semi-transparent dark background card
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (10 + box_w, 10 + box_h), (25, 25, 25), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Draw thin border around card
        cv2.rectangle(frame, (10, 10), (10 + box_w, 10 + box_h), (80, 80, 80), 1)

        # Draw HUD text
        cv2.putText(
            frame,
            hud_text,
            (10 + padding_x, 10 + padding_y + h1),
            self.font,
            0.55,
            (0, 255, 180),  # Bright mint/cyan for telemetry
            1,
            lineType=cv2.LINE_AA,
        )

        # Draw hint text
        cv2.putText(
            frame,
            hint_text,
            (10 + padding_x, 10 + (padding_y * 2) + h1 + h2 + 2),
            self.font,
            0.45,
            (190, 190, 190),  # Soft gray for instructions
            1,
            lineType=cv2.LINE_AA,
        )
