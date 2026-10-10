"""Multi-Object Tracker Adapter for LiveSight (Phase 2).

Integrates ByteTrack multi-object tracking with Ultralytics YOLO models.
Encapsulates tracker configuration, lifecycle management, safe resets,
and documents tracking limitations according to 02_SYSTEM_ARCHITECTURE.md.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Union

from vision.exceptions import VisionError


class TrackerError(VisionError):
    """Raised when tracker initialization, configuration, or tracking fails."""


class ByteTrackerAdapter:
    """ByteTrack tracker adapter managing tracker lifecycle and state resets.

    Important Track-ID Characteristics and Limitations:
    1. Scoped to Tracker Session: A track ID is ephemeral and valid only within
       the lifetime of a continuous video stream session.
    2. Stream Restart: When a video source restarts or reconnects, the tracker
       state must be reset, resetting track IDs.
    3. Occlusion and Lost Tracks: If a tracked object disappears for longer than
       `track_buffer` (default: 30 frames), ByteTrack drops the track. When the object
       re-emerges, it will be assigned a new track ID.
    4. ID Switching: Complex crossing paths, dense crowds, and low-confidence detections
       can lead to ID switches.
    """

    def __init__(
        self,
        tracker_config: Union[str, Path] = "bytetrack.yaml",
        persist: bool = True,
    ) -> None:
        """Initialize tracker adapter.

        Args:
            tracker_config: Name of built-in Ultralytics tracker ('bytetrack.yaml')
                            or path to custom tracker YAML config file.
            persist: Whether to preserve tracks between sequential frames.
        """
        self.tracker_config = str(tracker_config)
        self.persist = persist
        self._validate_config(tracker_config)

    def _validate_config(self, config: Union[str, Path]) -> None:
        """Validate tracker configuration parameter."""
        cfg_str = str(config).strip()
        if not cfg_str:
            raise TrackerError("Tracker configuration cannot be empty.")

        # If it's a file path with yaml extension, check if it exists
        path = Path(cfg_str)
        if (cfg_str.endswith(".yaml") or cfg_str.endswith(".yml")) and "/" in cfg_str:
            if not path.exists():
                raise TrackerError(
                    f"Tracker configuration file not found at '{cfg_str}'.\n"
                    "Actionable step: Check the file path or use 'bytetrack.yaml'."
                )

    def reset(self, model=None) -> None:
        """Safely reset all internal tracking state across tracker instances.

        Clears tracked, lost, and removed tracks and resets the global track ID counter.
        """
        if model is not None:
            # 1. Reset predictor-level trackers if model has an initialized predictor
            predictor = getattr(model, "predictor", None)
            if predictor is not None:
                trackers = getattr(predictor, "trackers", [])
                for trk in trackers:
                    if hasattr(trk, "reset") and callable(trk.reset):
                        try:
                            trk.reset()
                        except Exception:
                            pass

        # 2. Reset global STrack counter if available
        try:
            from ultralytics.trackers.byte_tracker import STrack
            if hasattr(STrack, "reset_id") and callable(STrack.reset_id):
                STrack.reset_id()
        except ImportError:
            pass

    def __repr__(self) -> str:
        return f"<ByteTrackerAdapter config='{self.tracker_config}' persist={self.persist}>"
