"""Video source adapter for LiveSight.

Supports:
- Local video files (mp4, avi, mov, mkv, etc.)
- Webcams / integrated cameras by device index (e.g., 0, 1)

Features:
- Actionable error diagnostics for missing files, unavailable webcams, and unsupported codecs
- Safe resource cleanup via context management (`with VideoSource(...) as src:`)
- Frame iteration protocol
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Iterator, Optional, Tuple, Union

import cv2
import numpy as np

from vision.exceptions import VideoSourceError


class VideoSource:
    """Adapter managing video capture from local files or webcams."""

    def __init__(self, source: Union[int, str] = 0) -> None:
        """Initialize the video source.

        Args:
            source: Webcam device index (e.g., 0, 1) or path to a local video file.
        """
        self.raw_source = source
        self.is_webcam: bool = False
        self.source_path: Optional[Path] = None
        self.device_index: Optional[int] = None
        self._cap: Optional[cv2.VideoCapture] = None

        self._parse_and_validate_source(source)
        self._open()

    def _parse_and_validate_source(self, source: Union[int, str]) -> None:
        """Determine whether source is a webcam index or a file path, and validate."""
        # Handle string representations of integers (e.g. "0")
        if isinstance(source, int):
            self.is_webcam = True
            self.device_index = source
            return

        if isinstance(source, str) and source.strip().isdigit():
            self.is_webcam = True
            self.device_index = int(source.strip())
            return

        # Local file source
        path = Path(source).expanduser().resolve()
        self.source_path = path

        if not path.exists():
            raise VideoSourceError(
                f"Video file not found at: '{source}' (resolved to '{path}').\n"
                "Actionable steps:\n"
                "  1. Check that the file path is typed correctly.\n"
                "  2. Verify that the video file exists in the directory.\n"
                "  3. Use an absolute path or path relative to the project root."
            )

        if not path.is_file():
            raise VideoSourceError(
                f"Path '{source}' is a directory, not a video file.\n"
                "Actionable step: Provide a path to an actual video file (e.g., sample.mp4)."
            )

        self.is_webcam = False

    def _open(self) -> None:
        """Open the video capture device or file with cv2.VideoCapture."""
        target = self.device_index if self.is_webcam else str(self.source_path)
        cap = cv2.VideoCapture(target)

        if not cap.isOpened():
            cap.release()
            if self.is_webcam:
                raise VideoSourceError(
                    f"Failed to open webcam at device index {self.device_index}.\n"
                    "Actionable steps:\n"
                    "  1. Confirm your webcam is plugged in and functional.\n"
                    "  2. On macOS, ensure Terminal/IDE has camera access:\n"
                    "     System Settings -> Privacy & Security -> Camera -> Enable for your Terminal/IDE.\n"
                    "  3. Ensure no other application (Zoom, FaceTime, Photo Booth, browser) is locking the webcam.\n"
                    "  4. Try an alternative camera index (e.g., --source 1)."
                )
            else:
                raise VideoSourceError(
                    f"OpenCV failed to open video file '{self.source_path}'.\n"
                    "Actionable steps:\n"
                    "  1. Ensure the file is not corrupted.\n"
                    "  2. Verify the video format is supported (H.264/MP4, AVI, MOV).\n"
                    "  3. Check file read permissions."
                )

        self._cap = cap

    @property
    def fps(self) -> float:
        """Get source frame rate (FPS). Returns 30.0 fallback if unavailable."""
        if not self._cap or not self._cap.isOpened():
            return 30.0
        val = self._cap.get(cv2.CAP_PROP_FPS)
        return float(val) if val and val > 0 else 30.0

    @property
    def width(self) -> int:
        """Get frame width in pixels."""
        if not self._cap or not self._cap.isOpened():
            return 0
        return int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    @property
    def height(self) -> int:
        """Get frame height in pixels."""
        if not self._cap or not self._cap.isOpened():
            return 0
        return int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    @property
    def frame_count(self) -> int:
        """Get total frame count (0 or -1 for live streams/webcams)."""
        if not self._cap or not self._cap.isOpened() or self.is_webcam:
            return -1
        return int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read the next frame from the video source.

        Returns:
            Tuple of (success: bool, frame: Optional[np.ndarray])
        """
        if self._cap is None or not self._cap.isOpened():
            return False, None

        ret, frame = self._cap.read()
        if not ret or frame is None:
            return False, None

        return True, frame

    def __iter__(self) -> Iterator[Tuple[int, np.ndarray]]:
        """Yield (frame_index, frame) until video stream ends."""
        frame_idx = 0
        while True:
            ret, frame = self.read()
            if not ret or frame is None:
                break
            yield frame_idx, frame
            frame_idx += 1

    def release(self) -> None:
        """Release underlying OpenCV VideoCapture resources."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> VideoSource:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()

    def __repr__(self) -> str:
        if self.is_webcam:
            return f"<VideoSource webcam index={self.device_index}>"
        return f"<VideoSource file='{self.source_path}'>"
