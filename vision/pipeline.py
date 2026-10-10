"""Modular Vision Pipeline coordinator for LiveSight Phase 1.

Orchestrates frame inference, detection normalization, FPS tracking, and visual annotation.
"""

from __future__ import annotations
import collections
import time
from typing import Deque, List, Optional, Tuple

import numpy as np

from vision.annotator import FrameAnnotator
from vision.detector import YOLODetector
from vision.schemas import Detection


class DetectionPipeline:
    """End-to-end detection and tracking pipeline coordinating detector, annotator, and FPS metrics."""

    def __init__(
        self,
        detector: YOLODetector,
        annotator: Optional[FrameAnnotator] = None,
        fps_window_size: int = 30,
        enable_tracking: bool = True,
        tracker_config: str = "bytetrack.yaml",
        rule_engine: Optional[Any] = None,
    ) -> None:
        """Initialize the detection pipeline.

        Args:
            detector: Configured YOLODetector instance.
            annotator: FrameAnnotator instance for drawing visualizations.
            fps_window_size: Number of recent frames to calculate rolling average FPS.
            enable_tracking: Whether to run ByteTrack multi-object tracking.
            tracker_config: Path or identifier for ByteTrack config ('bytetrack.yaml').
            rule_engine: Optional RuleEngine instance for evaluating domain events.
        """
        self.detector = detector
        self.annotator = annotator or FrameAnnotator()
        self.fps_window_size = fps_window_size
        self.enable_tracking = enable_tracking
        self.tracker_config = tracker_config
        self.rule_engine = rule_engine

        # Telemetry & Diagnostics
        self._frame_times: Deque[float] = collections.deque(maxlen=fps_window_size)
        self._total_frames: int = 0
        self._start_time: Optional[float] = None
        self._last_time: Optional[float] = None
        self._latest_events: List[Any] = []

    def reset_telemetry(self) -> None:
        """Reset performance counters."""
        self._frame_times.clear()
        self._total_frames = 0
        self._start_time = None
        self._last_time = None
        self._latest_events.clear()

    def reset_tracker(self) -> None:
        """Reset internal tracker state and rule engine when a stream restarts or loops."""
        self.detector.reset_tracker()
        if self.rule_engine is not None and hasattr(self.rule_engine, "reset"):
            self.rule_engine.reset()
        self._latest_events.clear()

    @property
    def latest_events(self) -> List[Any]:
        """Most recent domain events produced during the last processed frame."""
        return list(self._latest_events)

    @property
    def current_fps(self) -> float:
        """Get moving-average FPS based on recent frame intervals."""
        if not self._frame_times:
            return 0.0
        avg_dt = sum(self._frame_times) / len(self._frame_times)
        return 1.0 / avg_dt if avg_dt > 0 else 0.0

    @property
    def total_frames(self) -> int:
        """Total number of processed frames."""
        return self._total_frames

    @property
    def overall_average_fps(self) -> float:
        """Get lifetime average FPS since pipeline started."""
        if self._start_time is None or self._total_frames == 0:
            return 0.0
        elapsed = time.perf_counter() - self._start_time
        return self._total_frames / elapsed if elapsed > 0 else 0.0

    def process_frame(
        self,
        frame: np.ndarray,
        source_label: Optional[str] = None,
        draw_annotations: bool = True,
        return_events: bool = False,
    ) -> Union[
        Tuple[np.ndarray, List[Detection], float],
        Tuple[np.ndarray, List[Detection], float, List[Any]],
    ]:
        """Process a single frame: detect/track objects, evaluate rules, update FPS, annotate.

        Args:
            frame: Input image array (BGR format).
            source_label: Optional text identifying the stream/source for display.
            draw_annotations: Whether to draw bounding boxes, IDs, and HUD on output frame.
            return_events: If True, returns 4-tuple including latest_events; otherwise 3-tuple.

        Returns:
            Tuple of (annotated_frame, detections_list, current_fps) or with events list if requested.
        """
        now = time.perf_counter()
        if self._start_time is None:
            self._start_time = now

        if self._last_time is not None:
            dt = now - self._last_time
            if dt > 0:
                self._frame_times.append(dt)
        self._last_time = now
        self._total_frames += 1

        # 1. Run detection or tracking
        if self.enable_tracking:
            detections = self.detector.track(
                frame=frame,
                tracker=self.tracker_config,
                persist=True,
            )
        else:
            detections = self.detector.detect(frame)

        # 2. Evaluate rule engine if configured
        new_events: List[Any] = []
        if self.rule_engine is not None and hasattr(self.rule_engine, "process"):
            h, w = frame.shape[:2]
            new_events = self.rule_engine.process(
                detections=detections,
                frame_time=now,
                frame_idx=self._total_frames,
                frame_dims=(w, h),
                camera_id=source_label or "local_camera_01",
            )
        self._latest_events = new_events

        # 3. Compute FPS
        fps = self.current_fps

        # 4. Annotate if requested
        if draw_annotations:
            rules_to_draw = (
                self.rule_engine.rules
                if self.rule_engine and hasattr(self.rule_engine, "rules")
                else None
            )
            annotated_frame = self.annotator.annotate(
                frame=frame,
                detections=detections,
                fps=fps,
                source_label=source_label,
                rules=rules_to_draw,
                events=new_events,
            )
        else:
            annotated_frame = frame

        if return_events:
            return annotated_frame, detections, fps, new_events
        return annotated_frame, detections, fps


