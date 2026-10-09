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
    """End-to-end detection pipeline coordinating detector, annotator, and FPS metrics."""

    def __init__(
        self,
        detector: YOLODetector,
        annotator: Optional[FrameAnnotator] = None,
        fps_window_size: int = 30,
    ) -> None:
        """Initialize the detection pipeline.

        Args:
            detector: Configured YOLODetector instance.
            annotator: FrameAnnotator instance for drawing visualizations.
            fps_window_size: Number of recent frames to calculate rolling average FPS.
        """
        self.detector = detector
        self.annotator = annotator or FrameAnnotator()
        self.fps_window_size = fps_window_size

        # Telemetry & Diagnostics
        self._frame_times: Deque[float] = collections.deque(maxlen=fps_window_size)
        self._total_frames: int = 0
        self._start_time: Optional[float] = None
        self._last_time: Optional[float] = None

    def reset_telemetry(self) -> None:
        """Reset performance counters."""
        self._frame_times.clear()
        self._total_frames = 0
        self._start_time = None
        self._last_time = None

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
    ) -> Tuple[np.ndarray, List[Detection], float]:
        """Process a single frame: detect objects, update FPS, and optionally annotate.

        Args:
            frame: Input image array (BGR format).
            source_label: Optional text identifying the stream/source for display.
            draw_annotations: Whether to draw bounding boxes and HUD on the output frame.

        Returns:
            Tuple of (annotated_or_original_frame, detections_list, current_fps).
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

        # 1. Run detection
        detections = self.detector.detect(frame)

        # 2. Compute FPS
        fps = self.current_fps

        # 3. Annotate if requested
        if draw_annotations:
            annotated_frame = self.annotator.annotate(
                frame=frame,
                detections=detections,
                fps=fps,
                source_label=source_label,
            )
        else:
            annotated_frame = frame

        return annotated_frame, detections, fps
